import * as vscode from 'vscode';

export function getControlPanelHtml(webview: vscode.Webview, nonce: string): string {
    const cspSource = webview.cspSource;

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SpiBerry Control Panel</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            color: var(--vscode-foreground);
            padding: 0;
            margin: 0;
            user-select: none;
        }

        .section {
            border-bottom: 1px solid var(--vscode-panel-border);
        }

        .section-header {
            display: flex;
            align-items: center;
            padding: 4px 8px;
            cursor: pointer;
            background-color: var(--vscode-sideBar-background);
            font-weight: bold;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.5px;
        }

        .section-header:hover {
            background-color: var(--vscode-list-hoverBackground);
        }

        .section-header .icon {
            margin-right: 6px;
            transition: transform 0.1s ease-in-out;
        }

        .section.collapsed .section-header .icon {
            transform: rotate(0deg);
        }

        .section-content {
            padding: 8px 12px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .section.collapsed .section-content {
            display: none;
        }

        button {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 4px 10px;
            text-align: center;
            cursor: pointer;
            width: 100%;
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            border-radius: 2px;
        }

        button:hover {
            background-color: var(--vscode-button-hoverBackground);
        }

        button:focus {
            outline: 1px solid var(--vscode-focusBorder);
            outline-offset: 2px;
        }

        button:active {
            background-color: var(--vscode-button-secondaryHoverBackground);
        }

        .description {
            font-size: 12px;
            color: var(--vscode-descriptionForeground);
            margin-bottom: 4px;
        }

        .status-container {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            background-color: var(--vscode-sideBar-background);
            border-bottom: 1px solid var(--vscode-panel-border);
            font-size: 12px;
        }

        .status-indicator {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: var(--vscode-testing-iconUnsetColor);
        }

        .status-indicator.online {
            background-color: var(--vscode-debugIcon-startForeground);
            box-shadow: 0 0 4px var(--vscode-debugIcon-startForeground);
        }

        .status-indicator.transitioning {
            background-color: var(--vscode-notificationsWarningIcon-foreground);
            box-shadow: 0 0 4px var(--vscode-notificationsWarningIcon-foreground);
        }

        .status-indicator.inactive {
            background-color: var(--vscode-errorForeground);
            box-shadow: 0 0 4px var(--vscode-errorForeground);
        }

        .status-text {
            flex-grow: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .refresh-button {
            background: none;
            border: none;
            color: var(--vscode-foreground);
            cursor: pointer;
            padding: 2px;
            display: flex;
            align-items: center;
            justify-content: center;
            width: auto;
            border-radius: 4px;
        }

        .refresh-button:hover {
            background-color: var(--vscode-toolbar-hoverBackground);
        }

        .refresh-button svg {
            width: 14px;
            height: 14px;
        }
    </style>
</head>
<body>
    <div class="status-container">
        <div id="status-indicator" class="status-indicator"></div>
        <div id="status-text" class="status-text">Checking device...</div>
        <button id="refresh-status" class="refresh-button" title="Refresh Status">
            <svg viewBox="0 0 16 16" fill="currentColor"><path d="M13.6,2.3C12.2,0.9,10.2,0,8,0C3.6,0,0,3.6,0,8s3.6,8,8,8c3.7,0,6.8-2.5,7.7-6l-1.5-0.4C13.5,12.5,11,14.5,8,14.5c-3.6,0-6.5-2.9-6.5-6.5S4.4,1.5,8,1.5c1.8,0,3.4,0.7,4.6,1.9L10,6h6V0L13.6,2.3z"/></svg>
        </button>
    </div>

    <div class="section" id="device-section">
        <div class="section-header">
            <span class="icon">▼</span>
            <span>Device</span>
        </div>
        <div class="section-content">
            <div class="command-group">
                <button data-command="spiberry.setDeviceCredentials">Set Device Credentials</button>
            </div>
            <div class="command-group">
                <button data-command="spiberry.openSshConsole">Open SSH Console</button>
            </div>
        </div>
    </div>

    <div class="section" id="deployment-section">
        <div class="section-header">
            <span class="icon">▼</span>
            <span>Deployment</span>
        </div>
        <div class="section-content">
            <div class="command-group">
                <button data-command="spiberry.sendCodeToDevice">Send Code To Device</button>
            </div>
            <div class="command-group">
                <button data-command="spiberry.installSpiBerryEngine">Install SpiBerry Engine</button>
            </div>
        </div>
    </div>

    <div class="section" id="service-section">
        <div class="section-header">
            <span class="icon">▼</span>
            <span>Service</span>
        </div>
        <div class="section-content">
            <div class="command-group">
                <button data-command="spiberry.enableService">Enable Service</button>
            </div>
            <div class="command-group">
                <button data-command="spiberry.disableService">Disable Service</button>
            </div>
            <div class="command-group">
                <button data-command="spiberry.startService">Start Service</button>
            </div>
            <div class="command-group">
                <button data-command="spiberry.stopService">Stop Service</button>
            </div>
            <div class="command-group">
                <button data-command="spiberry.followServiceJournal">Follow Journal</button>
            </div>
        </div>
    </div>

    <div class="section" id="tools-section">
        <div class="section-header">
            <span class="icon">▼</span>
            <span>Tools</span>
        </div>
        <div class="section-content">
            <div class="command-group">
                <div class="description">IntelliSense for libraries.</div>
                <button data-command="spiberry.installTypings">Install Typings</button>
            </div>
            <div class="command-group">
                <div class="description">Add helper utility classes.</div>
                <button data-command="spiberry.insertRaspiUtilClasses">Insert Raspi Util Classes</button>
            </div>
            <div class="command-group">
                <div class="description">Open the remote image browser in the editor area.</div>
                <button data-command="spiberry.openVisionTools">Open Vision Tools</button>
            </div>
        </div>
    </div>

    <script nonce="${nonce}">
        const vscodeApi = acquireVsCodeApi();

        const statusIndicator = document.getElementById('status-indicator');
        const statusText = document.getElementById('status-text');
        const refreshBtn = document.getElementById('refresh-status');

        // Listen for messages from the extension
        window.addEventListener('message', event => {
            const message = event.data;
            if (message.type === 'status') {
                const { serviceStatus } = message.data;
                const normalizedStatus = typeof serviceStatus === 'string' ? serviceStatus.trim().toLowerCase() : 'unknown';

                if (normalizedStatus === 'active') {
                    statusText.textContent = 'Service: active';
                    statusIndicator.className = 'status-indicator online';
                    statusIndicator.title = 'Service is active';
                } else if (normalizedStatus === 'activating' || normalizedStatus === 'deactivating') {
                    statusText.textContent = 'Service: ' + normalizedStatus;
                    statusIndicator.className = 'status-indicator transitioning';
                    statusIndicator.title = 'Service is ' + normalizedStatus;
                } else if (normalizedStatus === 'inactive') {
                    statusText.textContent = 'Service: inactive';
                    statusIndicator.className = 'status-indicator inactive';
                    statusIndicator.title = 'Service is inactive';
                } else {
                    statusText.textContent = 'Service: ' + normalizedStatus;
                    statusIndicator.className = 'status-indicator inactive';
                    statusIndicator.title = 'Service status unavailable';
                }
            }
        });

        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                vscodeApi.postMessage({ command: 'spiberry.refreshStatus' });
            });
        }

        // Section Collapsing
        document.querySelectorAll('.section-header').forEach(header => {
            header.addEventListener('click', () => {
                const section = header.parentElement;
                section.classList.toggle('collapsed');
                const icon = header.querySelector('.icon');
                icon.textContent = section.classList.contains('collapsed') ? '▶' : '▼';
            });
        });

        // Command Execution
        const buttons = document.querySelectorAll('button[data-command]');
        buttons.forEach((button) => {
            button.addEventListener('click', () => {
                const command = button.getAttribute('data-command');
                if (command) {
                    vscodeApi.postMessage({ command });
                }
            });
        });
    </script>
</body>
</html>`;
}
