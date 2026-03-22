import * as vscode from 'vscode';
import { NodeSSH } from 'node-ssh';
import * as path from 'path';
import * as fs from 'fs';
import * as https from 'https';

const RELEASE_URL = "https://github.com/Efe-Cal/SpiBerryEngine/releases/latest/download/spiberry.pyz";

let statusBarItem: vscode.StatusBarItem;

async function checkDeviceReachability(sshConfig: any): Promise<boolean> {
    const ssh = new NodeSSH();
    try {
        await ssh.connect({
            ...sshConfig,
            readyTimeout: 5000,
            connTimeout: 5000
        });
        return true;
    } catch (error) {
        return false;
    } finally {
        ssh.dispose();
    }
}

async function updateStatusBar(context: vscode.ExtensionContext) {
    let credentials;
    try {
        credentials = await context.secrets.get('deviceCredentials');
    } catch (error) {
        console.error('Error getting credentials:', error);
        statusBarItem.hide();
        return;
    }

    if (!credentials) {
        statusBarItem.hide();
        return;
    }

    let sshConfig;
    try {
        sshConfig = JSON.parse(credentials);
    } catch (error) {
        console.error('Error parsing credentials:', error);
        statusBarItem.hide();
        return;
    }

    statusBarItem.text = `$(circle-large-outline) Checking ${sshConfig.host}...`;
    statusBarItem.show();

    const isReachable = await checkDeviceReachability(sshConfig);
    if (isReachable) {
        statusBarItem.text = `$(circle-filled) ${sshConfig.host}`;
        statusBarItem.color = new vscode.ThemeColor('debugIcon.startForeground'); // Green-ish
        statusBarItem.tooltip = 'Device is reachable';
    } else {
        statusBarItem.text = `$(circle-filled) ${sshConfig.host}`;
        statusBarItem.color = new vscode.ThemeColor('errorForeground'); // Red
        statusBarItem.tooltip = 'Device is unreachable';
    }
}

async function sendFileToDevice(localFilePath: string, remoteFilePath: string, sshConfig: { host: string; username: string; password: string }) {
    const ssh = new NodeSSH();
    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: "Sending file to remote device...",
        cancellable: false
    }, async (progress) => {
        try {
            await ssh.connect(sshConfig);
            await ssh.putFile(localFilePath, remoteFilePath);
            vscode.window.showInformationMessage(`Successfully sent ${path.basename(localFilePath)} to remote device!`);
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to send file: ${error.message}`);
        } finally {
            ssh.dispose(); // Always close the connection
        }
    });
}

async function createInteractiveSshTerminal(sshConnection: NodeSSH, initCommand: string | null = null) {
    // 1. Request the shell from your existing node-ssh instance
    // You can pass terminal options like 'xterm-256color'
    const shellStream = await sshConnection.requestShell({ term: 'xterm-256color' });
    if (initCommand) {
        shellStream.write(`${initCommand}\r\n`);
    }
    

    const writeEmitter = new vscode.EventEmitter<string>();

    const pty: vscode.Pseudoterminal = {
        onDidWrite: writeEmitter.event,
        
        // Fired when the terminal is opened in the UI
        open: () => {
            shellStream.on('data', (data: Buffer) => {
                writeEmitter.fire(data.toString());
            });

            shellStream.on('close', () => {
                writeEmitter.fire('\r\nConnection closed by remote host.\r\n');
            });

            shellStream.on('error', (err: any) => {
                const message = err && err.message ? err.message : String(err);
                writeEmitter.fire(`\r\nSSH shell error: ${message}\r\n`);
                shellStream.end();
                sshConnection.dispose();
            });
        },

        // Fired when the user types in the terminal
        handleInput: (data: string) => {
            shellStream.write(data);
        },

        // IMPORTANT: Tells the remote SSH server the terminal size
        setDimensions: (dimensions: vscode.TerminalDimensions) => {
            shellStream.setWindow(dimensions.rows, dimensions.columns, 0, 0);
        },

        close: () => {
            shellStream.end();
            sshConnection.dispose();
        }
    };

    const terminal = vscode.window.createTerminal({
        name: "SpiBerry installation",
        pty: pty
    });

    terminal.show();
}

function isRobotCodeFile(document: vscode.TextDocument): boolean {
    const code = document.getText();
    return /^import\s+(motor|motor_pair|hub|light_matrix|color)|from\s+hub\s+import/m.test(code);
}

export function activate(context: vscode.ExtensionContext) {

	console.log('Congratulations, your extension "spiberry" is now active!');

    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 1);
    statusBarItem.command = 'spiberry.setDeviceCredentials';
    context.subscriptions.push(statusBarItem);

    // Initial check
    updateStatusBar(context);

    // Periodic check every 15 seconds
    const interval = setInterval(() => updateStatusBar(context), 15000);
    context.subscriptions.push({ dispose: () => clearInterval(interval) });

    const saveListener = vscode.workspace.onDidSaveTextDocument((document) => {
        const autoSendOnSave = vscode.workspace.getConfiguration().get('spiberry.autoSendOnSave', false);
        if (!autoSendOnSave) {
            return;
        }
        const editor = vscode.window.activeTextEditor;
        if (editor && editor.document === document) {
            vscode.commands.executeCommand('spiberry.sendCodeToDevice');
        }
    });
    context.subscriptions.push(saveListener);


	const connect = vscode.commands.registerCommand('spiberry.setDeviceCredentials', async () => {

        const credentials: { host?: string; username?: string; password?: string } = {};

		const host = await vscode.window.showInputBox({
			prompt: 'Enter the IP address or hostname of the device to connect to',
			placeHolder: 'e.g., 192.168.1.2 or raspberrypi',
            validateInput: (value) => value.trim() === '' ? 'Hostname is required' : null
		});
        if (!host) {
            return;
        }
        credentials.host = host.trim();

        const username = await vscode.window.showInputBox({
            prompt: 'Enter the username for the device',
            placeHolder: 'e.g., pi',
            validateInput: (value) => value.trim() === '' ? 'Username is required' : null
        });
        if (!username) {
            return;
        }
        credentials.username = username.trim();

        const password = await vscode.window.showInputBox({
            prompt: 'Enter the password for the device',
            placeHolder: 'e.g., your_password',
            password: true,
            validateInput: (value) => value.trim() === '' ? 'Password is required' : null
        });
        if (!password) {
            return;
        }
        credentials.password = password;

        // Here you can store the credentials in a secure way
        await context.secrets.store('deviceCredentials', JSON.stringify(credentials)).then(() => {
            vscode.window.showInformationMessage('Device credentials saved successfully!');
            updateStatusBar(context);
        });

	});

	context.subscriptions.push(connect);

	const sendCodeCommand = vscode.commands.registerCommand('spiberry.sendCodeToDevice', async () => {

		const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active file to send.');
            return;
        }

        const localFilePath = editor.document.uri.fsPath;
        const fileName = path.basename(localFilePath);
        
        const credentials = await context.secrets.get('deviceCredentials');
        if (!credentials) {
            vscode.window.showErrorMessage('Device credentials not set. Please set them first using the status bar item.');
            vscode.commands.executeCommand('spiberry.setDeviceCredentials');
            return;
        }
        const sshConfig = JSON.parse(credentials);

        vscode.window.showInformationMessage('Sending code to device...');

        const username = sshConfig.username || 'pi';
        const remoteDirectory = `/home/${username}/spiberry`;
        const remoteFileName = isRobotCodeFile(editor.document) ? 'robot_code.py' : "raspi_functions/"+fileName;
        const remoteFilePath = `${remoteDirectory}/${remoteFileName}`;
        await sendFileToDevice(localFilePath, remoteFilePath, sshConfig);
	});

	context.subscriptions.push(sendCodeCommand);


    const install = vscode.commands.registerCommand('spiberry.installSpiBerryEngine', async () => {
        const ssh = new NodeSSH();
        
        const credentials = await context.secrets.get('deviceCredentials');
        if (!credentials) {
            vscode.window.showErrorMessage('Device credentials not set. Please set them first using the status bar item.');
            vscode.commands.executeCommand('spiberry.setDeviceCredentials');
            return;
        }

        vscode.window.showInformationMessage('Installing SpiBerry Engine on device...');
        const sshConfig = JSON.parse(credentials);

        // Download file to extension's directory first
        const localFilePath = path.join(context.extensionPath, 'spiberry.pyz');
        
        try {
            // Download the file locally using Node.js https
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: 'Downloading SpiBerry Engine...',
                cancellable: false
            }, async () => {
                return new Promise<void>((resolve, reject) => {
                    const downloadFile = (url: string) => {
                        https.get(url, (response) => {
                            if (response.statusCode === 301 || response.statusCode === 302) {
                                // Handle redirect
                                downloadFile(response.headers.location!);
                                return;
                            }
                            
                            if (response.statusCode !== 200) {
                                reject(new Error(`Failed to download: Status Code ${response.statusCode}`));
                                return;
                            }

                            const file = fs.createWriteStream(localFilePath);
                            response.pipe(file);
                            file.on('finish', () => {
                                file.close();
                                resolve();
                            });
                            file.on('error', (err) => {
                                fs.unlink(localFilePath, () => {});
                                reject(err);
                            });
                        }).on('error', (err) => {
                            fs.unlink(localFilePath, () => {});
                            reject(err);
                        });
                    };
                    downloadFile(RELEASE_URL);
                });
            });

            vscode.window.showInformationMessage('SpiBerry Engine downloaded locally. Uploading to device...');
            
            // Upload to device
            await ssh.connect(sshConfig);
            await ssh.putFile(localFilePath, '/home/' + sshConfig.username + '/spiberry.pyz');
            
            vscode.window.showInformationMessage('SpiBerry Engine uploaded successfully on the device!');
            createInteractiveSshTerminal(ssh, "sudo python ~/spiberry.pyz\r\n"+sshConfig.password + "\r\n");
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to install SpiBerry Engine: ${error.message}`);
            ssh.dispose();
        }

    });

    context.subscriptions.push(install);

    const dumpTypings = vscode.commands.registerCommand('spiberry.installTypings', async () => {
        
        // Ask user whether to install to workspace or global
        const choice = await vscode.window.showQuickPick(
            [
                { label: 'Workspace', description: 'Install typings for current workspace only' },
                { label: 'Global', description: 'Install typings globally for all Python projects' }
            ],
            {
                placeHolder: 'Where would you like to install the LEGO Spike Python typings?',
                title: 'Install LEGO Spike Python Typings'
            }
        );

        if (!choice) {
            return; // User cancelled
        }

        const isGlobal = choice.label === 'Global';
        const workspaceFolders = vscode.workspace.workspaceFolders;

        // For workspace install, we need a workspace folder
        if (!isGlobal && !workspaceFolders) {
            vscode.window.showErrorMessage('No workspace folder open. Use Global install instead.');
            return;
        }

        // Use extensionContext.extensionPath to find the source typings
        const sourceDir = path.join(context.extensionPath, 'typings');

        // Get the target directory and stubPath based on installation type
        let targetDir: string;
        let stubPath: string;

        if (isGlobal) {
            // For global installation, use VS Code's global storage path
            // We'll use the extension's globalStoragePath instead of workspace
            const globalStorageDir = context.globalStorageUri.fsPath;
            targetDir = path.join(globalStorageDir, 'typings');
            stubPath = targetDir;
        } else {
            const projectRoot = workspaceFolders![0].uri.fsPath;
            const vscodeDir = path.join(projectRoot, '.vscode');
            targetDir = path.join(vscodeDir, 'typings');
            stubPath = './.vscode/typings';
        }

        try {
            if (!fs.existsSync(targetDir)) {
                fs.mkdirSync(targetDir, { recursive: true });
            }

            const files = fs.readdirSync(sourceDir);
            for (const file of files) {
                const srcPath = path.join(sourceDir, file);
                const destPath = path.join(targetDir, file);
                fs.copyFileSync(srcPath, destPath);
            }

            // Determine configuration target
            const configTarget = isGlobal
                ? vscode.ConfigurationTarget.Global
                : vscode.ConfigurationTarget.Workspace;

            await vscode.workspace.getConfiguration('python.analysis').update(
                'stubPath',
                stubPath,
                configTarget
            );

            const location = isGlobal ? 'globally' : 'to .vscode/typings';
            vscode.window.showInformationMessage(`Successfully dumped SpiBerry typings ${location}`);
        } catch (err: any) {
            vscode.window.showErrorMessage(`Failed to dump typings: ${err.message}`);
        }
    });

    context.subscriptions.push(dumpTypings);
}

// This method is called when your extension is deactivated
export function deactivate() {}
