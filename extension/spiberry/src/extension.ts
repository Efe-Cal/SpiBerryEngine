import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import * as https from 'https';
import {
    checkDeviceReachabilityAndServiceStatus,
    createInteractiveSshTerminal,
    createSshConnection,
    sendFileToDevice,
    uploadFileOverSsh,
    type DeviceSshConfig
} from './sshUtils';
import { getControlPanelHtml } from './controlPanelHtml';

const RELEASE_URL = 'https://github.com/Efe-Cal/SpiBerryEngine/releases/latest/download/spiberry.pyz';

let statusBarItem: vscode.StatusBarItem;

class ControlPanelViewProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'spiberry.controlPanel';
    private _view?: vscode.WebviewView;

    constructor(private readonly context: vscode.ExtensionContext) {}

    resolveWebviewView(webviewView: vscode.WebviewView): void {
        this._view = webviewView;
        webviewView.webview.options = {
            enableScripts: true
        };

        webviewView.webview.html = getControlPanelHtml(webviewView.webview, this.getNonce());

        webviewView.webview.onDidReceiveMessage(async (message: { command?: string }) => {
            if (!message.command) {
                return;
            }

            if (message.command === 'spiberry.refreshStatus') {
                await this.updateStatus();
                return;
            }

            void vscode.commands.executeCommand(message.command);
        });

        // Initial status update
        this.updateStatus();
    }

    public async updateStatus(): Promise<void> {
        if (!this._view) {
            return;
        }

        const credentials = await this.context.secrets.get('deviceCredentials');
        if (!credentials) {
            this._view.webview.postMessage({ type: 'status', data: { serviceStatus: 'unknown' } });
            return;
        }

        const sshConfig = JSON.parse(credentials) as DeviceSshConfig;
        const [isReachable, serviceStatus] = await checkDeviceReachabilityAndServiceStatus(sshConfig);
        console.log(`Device ${sshConfig.host} reachable: ${isReachable}, service status: ${serviceStatus}`);
        this._view.webview.postMessage({
            type: 'status',
            data: {
                connected: isReachable,
                host: sshConfig.host,
                serviceStatus
            }
        });
    }

    private getNonce(): string {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let result = '';
        for (let i = 0; i < 32; i += 1) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }

        return result;
    }
}

async function updateStatusBar(context: vscode.ExtensionContext): Promise<void> {
    let credentials: string | undefined;
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

    let sshConfig: DeviceSshConfig;
    try {
        sshConfig = JSON.parse(credentials) as DeviceSshConfig;
    } catch (error) {
        console.error('Error parsing credentials:', error);
        statusBarItem.hide();
        return;
    }

    statusBarItem.text = `$(circle-large-outline) Checking ${sshConfig.host}...`;
    statusBarItem.show();

    const [isReachable, serviceStatus] = await checkDeviceReachabilityAndServiceStatus(sshConfig);
    if (isReachable) {
        statusBarItem.text = `$(circle-filled) ${sshConfig.host}`;
        statusBarItem.color = new vscode.ThemeColor('debugIcon.startForeground');
        statusBarItem.tooltip = `Device is reachable - Service: ${serviceStatus}`;
    } else {
        statusBarItem.text = `$(circle-filled) ${sshConfig.host}`;
        statusBarItem.color = new vscode.ThemeColor('errorForeground');
        statusBarItem.tooltip = 'Device is unreachable';
    }
}

function isRobotCodeFile(document: vscode.TextDocument): boolean {
    const code = document.getText();
    return /^import\s+(motor|motor_pair|hub|light_matrix|color)|from\s+hub\s+import/m.test(code);
}

function quoteForSingleQuotedShell(value: string): string {
    return `'${value.replace(/'/g, `'\\''`)}'`;
}

export function activate(context: vscode.ExtensionContext): void {
    console.log('Congratulations, your extension "spiberry" is now active!');

    const controlPanelProvider = new ControlPanelViewProvider(context);
    context.subscriptions.push(vscode.window.registerWebviewViewProvider(ControlPanelViewProvider.viewType, controlPanelProvider));

    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 1);
    statusBarItem.command = 'spiberry.setDeviceCredentials';
    context.subscriptions.push(statusBarItem);

    updateStatusBar(context);
    void controlPanelProvider.updateStatus();

    const interval = setInterval(() => {
        void updateStatusBar(context);
        void controlPanelProvider.updateStatus();
    }, 15000);
    context.subscriptions.push({ dispose: () => clearInterval(interval) });

    const saveListener = vscode.workspace.onDidSaveTextDocument((document) => {
        const autoSendOnSave = vscode.workspace.getConfiguration().get('spiberry.autoSendOnSave', false);
        if (!autoSendOnSave) {
            return;
        }
        const editor = vscode.window.activeTextEditor;
        if (editor && editor.document === document) {
            void vscode.commands.executeCommand('spiberry.sendCodeToDevice');
        }
    });
    context.subscriptions.push(saveListener);

    const connect = vscode.commands.registerCommand('spiberry.setDeviceCredentials', async () => {
        const credentials: { host?: string; username?: string; password?: string } = {};

        const host = await vscode.window.showInputBox({
            prompt: 'Enter the IP address or hostname of the device to connect to',
            placeHolder: 'e.g., 192.168.1.2 or raspberrypi',
            validateInput: (value) => (value.trim() === '' ? 'Hostname is required' : null)
        });
        if (!host) {
            return;
        }
        credentials.host = host.trim();

        const username = await vscode.window.showInputBox({
            prompt: 'Enter the username for the device',
            placeHolder: 'e.g., pi',
            validateInput: (value) => (value.trim() === '' ? 'Username is required' : null)
        });
        if (!username) {
            return;
        }
        credentials.username = username.trim();

        const password = await vscode.window.showInputBox({
            prompt: 'Enter the password for the device',
            placeHolder: 'e.g., your_password',
            password: true,
            validateInput: (value) => (value.trim() === '' ? 'Password is required' : null)
        });
        if (!password) {
            return;
        }
        credentials.password = password;

        await context.secrets.store('deviceCredentials', JSON.stringify(credentials));
        vscode.window.showInformationMessage('Device credentials saved successfully!');
        void updateStatusBar(context);
        void controlPanelProvider.updateStatus();
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
            void vscode.commands.executeCommand('spiberry.setDeviceCredentials');
            return;
        }

        const sshConfig = JSON.parse(credentials) as DeviceSshConfig;

        vscode.window.showInformationMessage('Sending code to device...');

        const username = sshConfig.username || 'pi';
        const remoteDirectory = `/home/${username}/spiberry`;
        const remoteFileName = isRobotCodeFile(editor.document) ? 'robot_code.py' : `raspi_functions/${fileName}`;
        const remoteFilePath = `${remoteDirectory}/${remoteFileName}`;

        await sendFileToDevice(localFilePath, remoteFilePath, sshConfig);
    });
    context.subscriptions.push(sendCodeCommand);

    const runServiceCommand = async (
        action: 'enable' | 'disable' | 'start' | 'stop',
        successMessage: string
    ): Promise<void> => {
        const credentials = await context.secrets.get('deviceCredentials');
        if (!credentials) {
            vscode.window.showErrorMessage('Device credentials not set. Please set them first using the status bar item.');
            void vscode.commands.executeCommand('spiberry.setDeviceCredentials');
            return;
        }

        const sshConfig = JSON.parse(credentials) as DeviceSshConfig;
        const escapedPassword = quoteForSingleQuotedShell(sshConfig.password);
        const command = `echo ${escapedPassword} | sudo -S systemctl ${action} sbe.service`;

        let sshConnection;
        try {
            sshConnection = await createSshConnection(sshConfig);
            const result = await sshConnection.execCommand(command);

            if (result.code !== 0) {
                const stderrOutput = result.stderr.trim() || 'Unknown error';
                vscode.window.showErrorMessage(`Failed to ${action} service: ${stderrOutput}`);
                return;
            }

            vscode.window.showInformationMessage(successMessage);
            void updateStatusBar(context);
            void controlPanelProvider.updateStatus();
        } catch (error: unknown) {
            const message = error instanceof Error ? error.message : String(error);
            vscode.window.showErrorMessage(`Failed to ${action} service: ${message}`);
        } finally {
            sshConnection?.dispose();
        }
    };

    const enableServiceCommand = vscode.commands.registerCommand('spiberry.enableService', async () => {
        await runServiceCommand('enable', 'Service enabled successfully.');
    });
    context.subscriptions.push(enableServiceCommand);

    const disableServiceCommand = vscode.commands.registerCommand('spiberry.disableService', async () => {
        await runServiceCommand('disable', 'Service disabled successfully.');
    });
    context.subscriptions.push(disableServiceCommand);

    const startServiceCommand = vscode.commands.registerCommand('spiberry.startService', async () => {
        await runServiceCommand('start', 'Service started successfully.');
    });
    context.subscriptions.push(startServiceCommand);

    const stopServiceCommand = vscode.commands.registerCommand('spiberry.stopService', async () => {
        await runServiceCommand('stop', 'Service stopped successfully.');
    });
    context.subscriptions.push(stopServiceCommand);

    const insertRaspiUtilClass = vscode.commands.registerCommand('spiberry.insertRaspiUtilClasses', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor found to insert into.');
            return;
        }

        const utilClassPath = path.join(context.extensionPath, 'raspi-util-class.py');
        if (!fs.existsSync(utilClassPath)) {
            vscode.window.showErrorMessage('Could not find raspi-util-class.py in the extension directory.');
            return;
        }

        try {
            const utilClassContent = fs.readFileSync(utilClassPath, 'utf8').replace(/\r?\n$/, '');
            const wrappedContent = ['# region spiberry: raspi util classes', utilClassContent, '# endregion', '','',''].join('\n');

            const inserted = await editor.edit((editBuilder) => {
                editBuilder.insert(new vscode.Position(0, 0), wrappedContent);
            });
            editor.selection = new vscode.Selection(new vscode.Position(0, 0), new vscode.Position(0, 0));
            vscode.commands.executeCommand('editor.fold');

            if (!inserted) {
                vscode.window.showErrorMessage('Failed to insert raspi util class content.');
                return;
            }

            vscode.window.showInformationMessage('Inserted raspi util class with region folding markers.');
        } catch (error: unknown) {
            const message = error instanceof Error ? error.message : String(error);
            vscode.window.showErrorMessage(`Failed to read or insert raspi util class: ${message}`);
        }
    });
    context.subscriptions.push(insertRaspiUtilClass);

    const install = vscode.commands.registerCommand('spiberry.installSpiBerryEngine', async () => {
        const credentials = await context.secrets.get('deviceCredentials');
        if (!credentials) {
            vscode.window.showErrorMessage('Device credentials not set. Please set them first using the status bar item.');
            void vscode.commands.executeCommand('spiberry.setDeviceCredentials');
            return;
        }

        vscode.window.showInformationMessage('Installing SpiBerry Engine on device...');
        const sshConfig = JSON.parse(credentials) as DeviceSshConfig;

        const localFilePath = path.join(context.extensionPath, 'spiberry.pyz');
        let sshConnection;

        try {
            await vscode.window.withProgress(
                {
                    location: vscode.ProgressLocation.Notification,
                    title: 'Downloading SpiBerry Engine...',
                    cancellable: false
                },
                async () =>
                    new Promise<void>((resolve, reject) => {
                        const downloadFile = (url: string) => {
                            https
                                .get(url, (response) => {
                                    if (response.statusCode === 301 || response.statusCode === 302) {
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
                                        fs.unlink(localFilePath, () => {
                                            // noop
                                        });
                                        reject(err);
                                    });
                                })
                                .on('error', (err) => {
                                    fs.unlink(localFilePath, () => {
                                        // noop
                                    });
                                    reject(err);
                                });
                        };

                        downloadFile(RELEASE_URL);
                    })
            );

            vscode.window.showInformationMessage('SpiBerry Engine downloaded locally. Uploading to device...');

            sshConnection = await createSshConnection(sshConfig);
            await uploadFileOverSsh(sshConnection, localFilePath, `/home/${sshConfig.username}/spiberry.pyz`);

            vscode.window.showInformationMessage('SpiBerry Engine uploaded successfully on the device!');
            await createInteractiveSshTerminal(sshConnection, `sudo python ~/spiberry.pyz\r\n${sshConfig.password}\r\n`, 'SpiBerry Installation');
        } catch (error: unknown) {
            const message = error instanceof Error ? error.message : String(error);
            vscode.window.showErrorMessage(`Failed to install SpiBerry Engine: ${message}`);
            if (sshConnection) {
                sshConnection.dispose();
            }
        }
    });
    context.subscriptions.push(install);

    const dumpTypings = vscode.commands.registerCommand('spiberry.installTypings', async () => {
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
            return;
        }

        const isGlobal = choice.label === 'Global';
        const workspaceFolders = vscode.workspace.workspaceFolders;

        if (!isGlobal && !workspaceFolders) {
            vscode.window.showErrorMessage('No workspace folder open. Use Global install instead.');
            return;
        }

        const sourceDir = path.join(context.extensionPath, 'typings');

        let targetDir: string;
        let stubPath: string;

        if (isGlobal) {
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

            const configTarget = isGlobal ? vscode.ConfigurationTarget.Global : vscode.ConfigurationTarget.Workspace;

            await vscode.workspace.getConfiguration('python.analysis').update('stubPath', stubPath, configTarget);

            const location = isGlobal ? 'globally' : 'to .vscode/typings';
            vscode.window.showInformationMessage(`Successfully dumped SpiBerry typings ${location}`);
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : String(err);
            vscode.window.showErrorMessage(`Failed to dump typings: ${message}`);
        }
    });
    context.subscriptions.push(dumpTypings);

    const openTerminalCommand = vscode.commands.registerCommand('spiberry.openSshConsole', async () => {
        const credentials = await context.secrets.get('deviceCredentials');
        if (!credentials) {
            vscode.window.showErrorMessage('Device credentials not set. Please set them first using the status bar item.');
            void vscode.commands.executeCommand('spiberry.setDeviceCredentials');
            return;
        }
        const sshConfig = JSON.parse(credentials) as DeviceSshConfig;
        try {
            const sshConnection = await createSshConnection(sshConfig);
            await createInteractiveSshTerminal(sshConnection, null, `ssh: ${sshConfig.host}`);
        } catch (error: unknown) {
            const message = error instanceof Error ? error.message : String(error);
            vscode.window.showErrorMessage(`Failed to open SSH console: ${message}`);
        }
    });

    context.subscriptions.push(openTerminalCommand);

    const followJournalCommand = vscode.commands.registerCommand('spiberry.followServiceJournal', async () => {
        const credentials = await context.secrets.get('deviceCredentials');
        if (!credentials) {
            vscode.window.showErrorMessage('Device credentials not set. Please set them first using the status bar item.');
            void vscode.commands.executeCommand('spiberry.setDeviceCredentials');
            return;
        }

        const sshConfig = JSON.parse(credentials) as DeviceSshConfig;
        try {
            const sshConnection = await createSshConnection(sshConfig);
            await createInteractiveSshTerminal(sshConnection, 'journalctl -fu sbe -o cat', `journal: ${sshConfig.host}`);
        } catch (error: unknown) {
            const message = error instanceof Error ? error.message : String(error);
            vscode.window.showErrorMessage(`Failed to open journal stream: ${message}`);
        }
    });

    context.subscriptions.push(followJournalCommand);
}

export function deactivate(): void {}
