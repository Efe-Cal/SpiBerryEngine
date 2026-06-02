import * as vscode from 'vscode';
import * as path from 'path';
import { listRemoteDirectory, loadRemoteImageDataUri, type DeviceSshConfig, type RemoteDirectoryEntry } from './sshUtils';
import { getVisionToolsHtml } from './visionToolsHtml';

export class VisionToolsPanel {
    public static currentPanel?: VisionToolsPanel;
    public static readonly viewType = 'spiberry.visionTools';

    private readonly _panel: vscode.WebviewPanel;
    private readonly _context: vscode.ExtensionContext;
    private _disposables: vscode.Disposable[] = [];

    public static createOrShow(context: vscode.ExtensionContext): void {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;

        // If we already have a panel, show it.
        if (VisionToolsPanel.currentPanel) {
            VisionToolsPanel.currentPanel._panel.reveal(column);
            return;
        }

        // Otherwise, create a new panel.
        const panel = vscode.window.createWebviewPanel(
            VisionToolsPanel.viewType,
            'SpiBerry Vision Tools',
            column || vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [
                    vscode.Uri.file(path.join(context.extensionPath, 'resources'))
                ]
            }
        );

        VisionToolsPanel.currentPanel = new VisionToolsPanel(panel, context);
    }

    private constructor(panel: vscode.WebviewPanel, context: vscode.ExtensionContext) {
        this._panel = panel;
        this._context = context;

        // Set the webview's initial html content
        this._update();

        // Listen for when the panel is disposed
        // This happens when the user closes the panel or when the panel is closed programmatically
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);

        // Handle messages from the webview
        this._panel.webview.onDidReceiveMessage(
            async (message: { command: string; path?: string; message?: string }) => {
                switch (message.command) {
                    case 'pick-image':
                        await this._handlePickImage();
                        break;
                    case 'reload-image':
                        if (typeof message.path === 'string') {
                            await this._handleReloadImage(message.path);
                        }
                        break;
                    case 'info':
                        if (typeof message.message === 'string') {
                            vscode.window.showInformationMessage(message.message);
                        }
                        break;
                }
            },
            null,
            this._disposables
        );
    }

    public dispose(): void {
        VisionToolsPanel.currentPanel = undefined;

        // Clean up our resources
        this._panel.dispose();

        while (this._disposables.length) {
            const x = this._disposables.pop();
            if (x) {
                x.dispose();
            }
        }
    }

    private _update(): void {
        const webview = this._panel.webview;
        this._panel.title = 'SpiBerry Vision Tools';
        webview.html = getVisionToolsHtml(webview, this._getNonce());
    }

    private _getNonce(): string {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let result = '';
        for (let i = 0; i < 32; i += 1) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    }

    private async _handlePickImage(): Promise<void> {
        const credentialsStr = await this._context.secrets.get('deviceCredentials');
        if (!credentialsStr) {
            vscode.window.showErrorMessage('Device credentials not set. Please configure them in the SpiBerry panel.');
            void vscode.commands.executeCommand('spiberry.setDeviceCredentials');
            this._panel.webview.postMessage({ type: 'error', message: 'Device credentials not configured.' });
            return;
        }

        let sshConfig: DeviceSshConfig;
        try {
            sshConfig = JSON.parse(credentialsStr) as DeviceSshConfig;
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : String(err);
            vscode.window.showErrorMessage(`Failed to parse saved credentials: ${message}`);
            return;
        }

        const username = sshConfig.username || 'pi';
        let currentRemoteDir = `/home/${username}/spiberry`;

        let activePathValid = false;
        
        while (true) {
            let entries: RemoteDirectoryEntry[] = [];
            
            try {
                entries = await vscode.window.withProgress(
                    {
                        location: vscode.ProgressLocation.Notification,
                        title: `Connecting and scanning: ${currentRemoteDir}`,
                        cancellable: true
                    },
                    async (progress, token) => {
                        if (token.isCancellationRequested) {
                            throw new Error('Cancelled');
                        }
                        return listRemoteDirectory(sshConfig, currentRemoteDir);
                    }
                );
                activePathValid = true;
            } catch (error: unknown) {
                const message = error instanceof Error ? error.message : String(error);
                if (message === 'Cancelled') {
                    return; // user cancelled the progress
                }
                
                // If the default folder doesn't exist, let's fallback to /home/pi (or username) once.
                if (!activePathValid && currentRemoteDir === `/home/${username}/spiberry`) {
                    currentRemoteDir = `/home/${username}`;
                    activePathValid = true;
                    continue;
                }

                vscode.window.showErrorMessage(`Failed to list remote folder: ${message}`);
                this._panel.webview.postMessage({ type: 'error', message: `SSH error: ${message}` });
                return;
            }

            const items: vscode.QuickPickItem[] = [];

            // Add Go Back option if not at the root home dir or absolute root
            if (currentRemoteDir !== '/' && currentRemoteDir !== `/home/${username}`) {
                items.push({
                    label: '$(arrow-left) ..',
                    description: 'Go back to parent directory',
                    detail: path.posix.dirname(currentRemoteDir)
                });
            }

            for (const entry of entries) {
                if (entry.type === 'directory') {
                    items.push({
                        label: `$(folder) ${entry.name}`,
                        description: 'Directory',
                        detail: entry.path
                    });
                } else if (entry.isImage) {
                    items.push({
                        label: `$(file-media) ${entry.name}`,
                        description: 'Image File',
                        detail: entry.path
                    });
                }
            }

            if (items.length === 0) {
                items.push({
                    label: '$(info) No images or subdirectories found',
                    description: '',
                    detail: ''
                });
            }

            const selection = await vscode.window.showQuickPick(items, {
                placeHolder: `Select an image or sub-folder in ${currentRemoteDir}`,
                title: 'SpiBerry Remote Image Picker'
            });

            if (!selection) {
                return; // User cancelled
            }

            if (selection.label === '$(info) No images or subdirectories found') {
                if (currentRemoteDir !== `/home/${username}`) {
                    currentRemoteDir = path.posix.dirname(currentRemoteDir);
                    continue;
                }
                return;
            }

            if (selection.label === '$(arrow-left) ..') {
                currentRemoteDir = selection.detail!;
                continue;
            }

            const matchedEntry = entries.find((e) => e.path === selection.detail);
            if (!matchedEntry) {
                continue;
            }

            if (matchedEntry.type === 'directory') {
                currentRemoteDir = matchedEntry.path;
            } else {
                // We got our remote image path! Let's download and post to webview
                await this._loadAndPostImage(sshConfig, matchedEntry);
                break;
            }
        }
    }

    private async _handleReloadImage(remoteImagePath: string): Promise<void> {
        const credentialsStr = await this._context.secrets.get('deviceCredentials');
        if (!credentialsStr) {
            vscode.window.showErrorMessage('Device credentials not set.');
            return;
        }

        let sshConfig: DeviceSshConfig;
        try {
            sshConfig = JSON.parse(credentialsStr) as DeviceSshConfig;
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : String(err);
            vscode.window.showErrorMessage(`Failed to parse saved credentials: ${message}`);
            return;
        }

        const name = path.posix.basename(remoteImagePath);
        const dummyEntry: RemoteDirectoryEntry = {
            name,
            path: remoteImagePath,
            type: 'file',
            isImage: true
        };

        await this._loadAndPostImage(sshConfig, dummyEntry);
    }

    private async _loadAndPostImage(sshConfig: DeviceSshConfig, entry: RemoteDirectoryEntry): Promise<void> {
        this._panel.webview.postMessage({ type: 'loading', text: `Fetching remote image over SSH: ${entry.name}...` });

        try {
            const dataUri = await loadRemoteImageDataUri(sshConfig, entry.path);
            this._panel.webview.postMessage({
                type: 'show-image',
                data: {
                    name: entry.name,
                    path: entry.path,
                    dataUri
                }
            });
        } catch (error: unknown) {
            const message = error instanceof Error ? error.message : String(error);
            vscode.window.showErrorMessage(`Failed to retrieve remote image: ${message}`);
            this._panel.webview.postMessage({ type: 'error', message: `Asset download failed: ${message}` });
        } finally {
            this._panel.webview.postMessage({ type: 'loading-finished' });
        }
    }
}
