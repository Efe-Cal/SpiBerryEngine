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
const REMOTE_CONFIG_FILE_NAME = 'spiberry_config.ini';
const DEFAULT_ROBOT_CODE_PATH = 'robot_code.py';
const DEFAULT_RASPI_FUNCTIONS_PATH = 'raspi_functions/';

let statusBarItem: vscode.StatusBarItem;

type UploadPathConfigSource = 'device-config' | 'defaults';

interface UploadPathConfig {
    robotCodePath: string;
    raspiFunctionsPath: string;
    source: UploadPathConfigSource;
    configPath: string;
}

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

function stripSpiberryBasePrefix(value: string): string {
    const normalized = value.replace(/\\/g, '/').trim();
    const match = normalized.match(/^(?:~\/spiberry\/|\/home\/[^/]+\/spiberry\/|spiberry\/)(.+)$/);
    return match ? match[1] : normalized;
}

function sanitizeRelativeRemotePath(value: string | undefined, fallback: string): string {
    const rawValue = value?.trim() ?? '';
    const candidate = rawValue === '' ? fallback : rawValue;
    const stripped = stripSpiberryBasePrefix(candidate);
    const cleaned = stripped
        .replace(/\\/g, '/')
        .split('/')
        .map((segment) => segment.trim())
        .filter((segment) => segment !== '' && segment !== '.' && segment !== '..');
    if (cleaned.length === 0) {
        return fallback.replace(/\\/g, '/').replace(/\/+$/, '');
    }
    return cleaned.join('/');
}

function sanitizeRaspiFunctionsDirectory(value: string | undefined): string {
    let directory = sanitizeRelativeRemotePath(value, DEFAULT_RASPI_FUNCTIONS_PATH);

    if (directory.toLowerCase().endsWith('.py')) {
        directory = path.posix.dirname(directory);
    }
    if (directory === '.' || directory === '') {
        directory = 'raspi_functions';
    }

    return directory.replace(/\/+$/, '');
}

function parseCodeSectionFromIni(content: string): { path?: string; raspi_functions_path?: string } {
    const result: { path?: string; raspi_functions_path?: string } = {};
    const lines = content.split(/\r?\n/);
    let inCodeSection = false;

    for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith(';') || trimmed.startsWith('#')) {
            continue;
        }

        const sectionMatch = trimmed.match(/^\[(.+)\]$/);
        if (sectionMatch) {
            inCodeSection = sectionMatch[1].trim().toLowerCase() === 'code';
            continue;
        }

        if (!inCodeSection) {
            continue;
        }

        const separatorIndex = trimmed.indexOf('=');
        if (separatorIndex < 0) {
            continue;
        }

        const key = trimmed.slice(0, separatorIndex).trim().toLowerCase();
        let value = trimmed.slice(separatorIndex + 1).trim();
        if (
            (value.startsWith('"') && value.endsWith('"'))
            || (value.startsWith("'") && value.endsWith("'"))
        ) {
            value = value.slice(1, -1);
        }

        if (key === 'path') {
            result.path = value;
        }
        if (key === 'raspi_functions_path') {
            result.raspi_functions_path = value;
        }
    }

    return result;
}

function getRemoteConfigFilePath(username: string): string {
    return `/home/${username}/${REMOTE_CONFIG_FILE_NAME}`;
}

async function resolveUploadPathConfig(sshConfig: DeviceSshConfig): Promise<UploadPathConfig> {
    const username = sshConfig.username || 'pi';
    const configPath = getRemoteConfigFilePath(username);

    const defaults = {
        robotCodePath: sanitizeRelativeRemotePath(DEFAULT_ROBOT_CODE_PATH, DEFAULT_ROBOT_CODE_PATH),
        raspiFunctionsPath: sanitizeRaspiFunctionsDirectory(DEFAULT_RASPI_FUNCTIONS_PATH),
        source: 'defaults' as UploadPathConfigSource,
        configPath
    };

    let sshConnection;
    try {
        sshConnection = await createSshConnection(sshConfig);
        const command = `cat ${quoteForSingleQuotedShell(configPath)}`;
        const result = await sshConnection.execCommand(command);

        if (typeof result.code === 'number' && result.code !== 0) {
            const stderr = result.stderr?.trim() || 'unknown error';
            vscode.window.showWarningMessage(`Could not read ${configPath} on device. Using default upload paths. (${stderr})`);
            return defaults;
        }

        const codeSection = parseCodeSectionFromIni(result.stdout ?? '');
        return {
            robotCodePath: sanitizeRelativeRemotePath(codeSection.path ?? defaults.robotCodePath, DEFAULT_ROBOT_CODE_PATH),
            raspiFunctionsPath: sanitizeRaspiFunctionsDirectory(codeSection.raspi_functions_path ?? defaults.raspiFunctionsPath),
            source: 'device-config',
            configPath
        };
    } catch (error: unknown) {
        const message = error instanceof Error ? error.message : String(error);
        vscode.window.showWarningMessage(`Failed to read device config over SSH. Using default upload paths. (${message})`);
        return defaults;
    } finally {
        sshConnection?.dispose();
    }
}

function joinRemotePath(...segments: string[]): string {
    const normalizedSegments = segments
        .map((segment) => segment.replace(/\\/g, '/').trim())
        .filter((segment) => segment !== '');
    return path.posix.join(...normalizedSegments);
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

    let callStatusBarNext = true;
    const interval = setInterval(() => {
        if (callStatusBarNext) {
            void updateStatusBar(context);
        } else {
            void controlPanelProvider.updateStatus();
        }
        callStatusBarNext = !callStatusBarNext;
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

        const uploadPathConfig = await resolveUploadPathConfig(sshConfig);

        const username = sshConfig.username || 'pi';
        const remoteDirectory = `/home/${username}/spiberry`;
        const remoteRobotCodePath = joinRemotePath(remoteDirectory, uploadPathConfig.robotCodePath);
        const remoteRaspiFunctionsDirectory = joinRemotePath(remoteDirectory, uploadPathConfig.raspiFunctionsPath);
        const remoteFilePath = isRobotCodeFile(editor.document)
            ? remoteRobotCodePath
            : joinRemotePath(remoteRaspiFunctionsDirectory, fileName);

        if (uploadPathConfig.source === 'device-config') {
            console.log(`Using upload paths from ${uploadPathConfig.configPath}`);
        } else {
            console.log('Using default upload paths (device config unavailable).');
        }

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
            void vscode.commands.executeCommand('editor.fold');

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
