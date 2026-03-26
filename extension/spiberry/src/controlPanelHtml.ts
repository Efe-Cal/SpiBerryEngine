import * as vscode from 'vscode';

export function getControlPanelHtml(webview: vscode.Webview, nonce: string): string {
    const cspSource = webview.cspSource;

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${cspSource}; script-src 'nonce-${nonce}';">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SpiBerry Control Panel</title>
    <style>
        :root {
            color-scheme: light dark;
        }

        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            color: var(--vscode-foreground);
            background: var(--vscode-sideBar-background);
            padding: 8px;
            margin: 0;
        }

        .menu {
            border: 1px solid var(--vscode-panel-border);
            border-radius: 6px;
            margin-bottom: 8px;
            overflow: hidden;
            background: var(--vscode-editorWidget-background);
        }

        summary {
            cursor: pointer;
            padding: 10px;
            font-weight: 600;
            user-select: none;
            list-style: none;
        }

        summary::-webkit-details-marker {
            display: none;
        }

        .content {
            padding: 0 10px 10px;
            display: grid;
            gap: 8px;
        }

        button {
            width: 100%;
            border: 1px solid var(--vscode-button-border, transparent);
            border-radius: 4px;
            padding: 6px 8px;
            text-align: left;
            cursor: pointer;
            color: var(--vscode-button-foreground);
            background: var(--vscode-button-background);
        }

        button:hover {
            background: var(--vscode-button-hoverBackground);
        }
    </style>
</head>
<body>
    <details class="menu" open>
        <summary>Device</summary>
        <div class="content">
            <button data-command="spiberry.setDeviceCredentials">Set Device Credentials</button>
            <button data-command="spiberry.refreshStatus">Refresh Device Status</button>
        </div>
    </details>

    <details class="menu" open>
        <summary>Deployment</summary>
        <div class="content">
            <button data-command="spiberry.sendCodeToDevice">Send Code To Device</button>
            <button data-command="spiberry.installSpiBerryEngine">Install SpiBerry Engine</button>
        </div>
    </details>

    <details class="menu" open>
        <summary>Tools</summary>
        <div class="content">
            <button data-command="spiberry.installTypings">Install Typings</button>
            <button data-command="spiberry.insertRaspiUtilClasses">Insert Raspi Util Classes</button>
        </div>
    </details>

    <script nonce="${nonce}">
        const vscodeApi = acquireVsCodeApi();
        const buttons = document.querySelectorAll('button[data-command]');
        buttons.forEach((button) => {
            button.addEventListener('click', () => {
                const command = button.getAttribute('data-command');
                if (!command) {
                    return;
                }

                vscodeApi.postMessage({ command });
            });
        });
    </script>
</body>
</html>`;
}
