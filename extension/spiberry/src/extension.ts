import * as vscode from 'vscode';
import { NodeSSH } from 'node-ssh';
import * as path from 'path';

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
    const credentials = await context.secrets.get('deviceCredentials');
    if (!credentials) {
        statusBarItem.hide();
        return;
    }

    const sshConfig = JSON.parse(credentials);
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
        const autoSendOnSave = vscode.workspace.getConfiguration().get('spiberry.autoSendOnSave', true);
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
		});
        if (host) {
            credentials.host = host;
        }

        const username = await vscode.window.showInputBox({
            prompt: 'Enter the username for the device',
            placeHolder: 'e.g., pi',
        });
        if (username) {
            credentials.username = username;
        }

        const password = await vscode.window.showInputBox({
            prompt: 'Enter the password for the device',
            placeHolder: 'e.g., your_password',
            password: true,
        });
        if (password) {
            credentials.password = password;
        }

        // Here you can store the credentials in a secure way
        await context.secrets.store('deviceCredentials', JSON.stringify(credentials)).then(() => {
            vscode.window.showInformationMessage('Device credentials saved successfully!');
            updateStatusBar(context);
        })

	});

	context.subscriptions.push(connect);

	const sendCodeCommand = vscode.commands.registerCommand('spiberry.sendCodeToDevice', async () => {

		vscode.window.showInformationMessage('Sending code to device...');

		const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active file to send.');
            return;
        }

        const localFilePath = editor.document.uri.fsPath;
        const fileName = path.basename(localFilePath);
        
        const sshConfig = await context.secrets.get('deviceCredentials').then((credentials) => {
            if (!credentials) {
                vscode.window.showErrorMessage('Device credentials not set. Please set them first.');
                return;
            }
            return JSON.parse(credentials);
        });

        if (!sshConfig) {
            return;
        }

        const username = (sshConfig as any).username || 'pi';
        const remoteDirectory = `/home/${username}/spiberry`;
        const remoteFileName = isRobotCodeFile(editor.document) ? 'robot_code.py' : fileName;
        const remoteFilePath = `${remoteDirectory}/${remoteFileName}`;
        await sendFileToDevice(localFilePath, remoteFilePath, sshConfig);
	});

	context.subscriptions.push(sendCodeCommand);


    const install = vscode.commands.registerCommand('spiberry.installSpiBerryEngine', async () => {
        const ssh = new NodeSSH();
        
        vscode.window.showInformationMessage('Installing SpiBerry Engine on device...');
        const sshConfig = await context.secrets.get('deviceCredentials').then((credentials) => {
            if (!credentials) {
                vscode.window.showErrorMessage('Device credentials not set. Please set them first.');
                return;
            }
            return JSON.parse(credentials);
        });

        const downloadCommand = `curl -L ${RELEASE_URL} -O`;
        let result;
        try {
            await ssh.connect(sshConfig)
            result = await ssh.execCommand(downloadCommand)
            if (result.code === 0) {
                vscode.window.showInformationMessage('SpiBerry Engine downloaded successfully on the device!');
                createInteractiveSshTerminal(ssh, "python ~/spiberry.pyz");
            } else {
                vscode.window.showErrorMessage(`Failed to download SpiBerry Engine: ${result.stderr}`);
            }
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to connect to device: ${error.message}`);
        } finally {
            if (result && result.code !== 0) {
                ssh.dispose();
            }
        }

    });

    context.subscriptions.push(install);
}

// This method is called when your extension is deactivated
export function deactivate() {}
