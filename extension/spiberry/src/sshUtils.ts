import * as vscode from 'vscode';
import { NodeSSH } from 'node-ssh';
import * as path from 'path';

export interface DeviceSshConfig {
    host: string;
    username: string;
    password: string;
}

export async function checkDeviceReachabilityAndServiceStatus(sshConfig: DeviceSshConfig): Promise<[boolean, string]> {
    const ssh = new NodeSSH();
    try {
        await ssh.connect({
            ...sshConfig,
            readyTimeout: 5000
        });
        const serviceStatus = await ssh.execCommand('systemctl is-active sbe.service');

        return [true, serviceStatus.stdout.trim()];
    } catch {
        return [false, 'unknown'];
    } finally {
        ssh.dispose();
    }
}

export async function sendFileToDevice(
    localFilePath: string,
    remoteFilePath: string,
    sshConfig: DeviceSshConfig
): Promise<void> {
    const ssh = new NodeSSH();
    await vscode.window.withProgress(
        {
            location: vscode.ProgressLocation.Notification,
            title: 'Sending file to remote device...',
            cancellable: false
        },
        async () => {
            try {
                await ssh.connect(sshConfig);
                await ssh.putFile(localFilePath, remoteFilePath);
                vscode.window.showInformationMessage(`Successfully sent ${path.basename(localFilePath)} to remote device!`);
            } catch (error: unknown) {
                const message = error instanceof Error ? error.message : String(error);
                vscode.window.showErrorMessage(`Failed to send file: ${message}`);
            } finally {
                ssh.dispose();
            }
        }
    );
}

export async function createSshConnection(sshConfig: DeviceSshConfig): Promise<NodeSSH> {
    const ssh = new NodeSSH();
    await ssh.connect(sshConfig);
    return ssh;
}

export async function uploadFileOverSsh(sshConnection: NodeSSH, localFilePath: string, remoteFilePath: string): Promise<void> {
    await sshConnection.putFile(localFilePath, remoteFilePath);
}

export async function createInteractiveSshTerminal(sshConnection: NodeSSH, initCommand: string | null = null, terminalName: string = 'SpiBerry Terminal'): Promise<void> {
    const shellStream = await sshConnection.requestShell({ term: 'xterm-256color' });
    if (initCommand) {
        shellStream.write(`${initCommand}\r\n`);
    }

    const writeEmitter = new vscode.EventEmitter<string>();

    const pty: vscode.Pseudoterminal = {
        onDidWrite: writeEmitter.event,
        open: () => {
            shellStream.on('data', (data: Buffer) => {
                writeEmitter.fire(data.toString());
            });

            shellStream.on('close', () => {
                writeEmitter.fire('\r\nConnection closed by remote host.\r\n');
            });

            shellStream.on('error', (err: unknown) => {
                const message = err instanceof Error ? err.message : String(err);
                writeEmitter.fire(`\r\nSSH shell error: ${message}\r\n`);
                shellStream.end();
                sshConnection.dispose();
            });
        },
        handleInput: (data: string) => {
            shellStream.write(data);
        },
        setDimensions: (dimensions: vscode.TerminalDimensions) => {
            shellStream.setWindow(dimensions.rows, dimensions.columns, 0, 0);
        },
        close: () => {
            shellStream.end();
            sshConnection.dispose();
        }
    };

    const terminal = vscode.window.createTerminal({
        name: terminalName,
        pty
    });

    terminal.show();
}