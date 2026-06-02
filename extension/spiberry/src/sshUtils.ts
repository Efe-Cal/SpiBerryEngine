import * as vscode from 'vscode';
import { NodeSSH } from 'node-ssh';
import * as path from 'path';
import * as os from 'os';
import * as fs from 'fs';

export interface DeviceSshConfig {
    host: string;
    username: string;
    password: string;
}

export interface RemoteDirectoryEntry {
    name: string;
    path: string;
    type: 'file' | 'directory';
    isImage: boolean;
}

function quoteForSingleQuotedShell(value: string): string {
    return `'${value.replace(/'/g, `'\\''`)}'`;
}

export async function checkDeviceReachabilityAndServiceStatus(sshConfig: DeviceSshConfig): Promise<[boolean, string]> {
    const ssh = new NodeSSH();
    try {
        await ssh.connect({
            ...sshConfig,
            readyTimeout: 5000
        });
        const serviceStatus = await ssh.execCommand('systemctl is-active sbe.service');

        const stdout = serviceStatus.stdout ? serviceStatus.stdout.trim() : '';
        const stderr = (serviceStatus as { stderr?: string }).stderr ? (serviceStatus as { stderr?: string }).stderr!.trim() : '';

        if (typeof serviceStatus.code === 'number' && serviceStatus.code !== 0) {
            // Command failed; device is reachable but service status could not be determined reliably.
            return [true, stderr || 'unknown'];
        }

        if (!stdout) {
            // No usable stdout; fall back to stderr message if available, otherwise 'unknown'.
            return [true, stderr || 'unknown'];
        }

        return [true, stdout];
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
                const remoteDirectory = path.posix.dirname(remoteFilePath);
                const mkdirResult = await ssh.execCommand(`mkdir -p ${quoteForSingleQuotedShell(remoteDirectory)}`);
                if (typeof mkdirResult.code === 'number' && mkdirResult.code !== 0) {
                    const stderr = mkdirResult.stderr?.trim() || 'unknown error';
                    throw new Error(`Failed to create remote directory ${remoteDirectory}: ${stderr}`);
                }
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

export async function listRemoteDirectory(
    sshConfig: DeviceSshConfig,
    remotePath: string
): Promise<RemoteDirectoryEntry[]> {
    const ssh = await createSshConnection(sshConfig);

    try {
        const normalizedPath = path.posix.normalize(remotePath.replace(/\\/g, '/'));
        const command = `if [ -d ${quoteForSingleQuotedShell(normalizedPath)} ]; then LC_ALL=C ls -1ApA ${quoteForSingleQuotedShell(normalizedPath)}; else echo "__SPIBERRY_NOT_A_DIRECTORY__" 1>&2; exit 2; fi`;
        const result = await ssh.execCommand(command);

        if (typeof result.code === 'number' && result.code !== 0) {
            const stderr = result.stderr?.trim() || 'unknown error';
            throw new Error(stderr);
        }

        return (result.stdout ?? '')
            .split(/\r?\n/)
            .filter((line) => line !== '')
            .map((line) => {
                const isDirectory = line.endsWith('/');
                const name = isDirectory ? line.slice(0, -1) : line;
                const fullPath = path.posix.join(normalizedPath, name);
                const extension = path.posix.extname(name).toLowerCase();
                const isImage = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp'].includes(extension);

                return {
                    name,
                    path: fullPath,
                    type: isDirectory ? 'directory' : 'file',
                    isImage
                } satisfies RemoteDirectoryEntry;
            })
            .sort((left, right) => {
                if (left.type !== right.type) {
                    return left.type === 'directory' ? -1 : 1;
                }

                return left.name.localeCompare(right.name);
            });
    } finally {
        ssh.dispose();
    }
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

export async function loadRemoteImageDataUri(sshConfig: DeviceSshConfig, remoteImagePath: string): Promise<string> {
    const ssh = await createSshConnection(sshConfig);
    const tempFilePath = path.join(
        os.tmpdir(),
        `spiberry-vision-${Date.now()}-${Math.random().toString(36).slice(2)}${path.extname(remoteImagePath) || '.img'}`
    );

    try {
        await ssh.getFile(tempFilePath, remoteImagePath);

        const fileBuffer = await fs.promises.readFile(tempFilePath);
        const ext = path.extname(remoteImagePath).toLowerCase().replace('.', '');
        const mimeType = ext === 'jpg' ? 'jpeg' : (ext || 'png');

        return `data:image/${mimeType};base64,${fileBuffer.toString('base64')}`;
    } finally {
        ssh.dispose();
        await fs.promises.rm(tempFilePath, { force: true });
    }
}
