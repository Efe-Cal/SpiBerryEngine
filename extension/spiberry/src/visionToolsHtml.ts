import * as vscode from 'vscode';

export function getVisionToolsHtml(webview: vscode.Webview, nonce: string): string {
    const cspSource = webview.cspSource;

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${cspSource} 'unsafe-inline'; img-src ${cspSource} data:; script-src 'nonce-${nonce}';">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SpiBerry Vision Tools</title>
    <style>
        body {
            font-family: var(--vscode-font-family, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif);
            font-size: var(--vscode-font-size, 13px);
            background-color: var(--vscode-editor-background, #1e1e1e);
            color: var(--vscode-editor-foreground, #d4d4d4);
            margin: 0;
            padding: 0;
            height: 100vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            user-select: none;
        }

        /* Loading Overlay */
        .loader-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(30, 30, 30, 0.8);
            z-index: 1000;
            display: none;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            gap: 16px;
        }

        .loader-spinner {
            width: 40px;
            height: 40px;
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top: 3px solid var(--vscode-progressBar-background, #007acc);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        .loader-text {
            font-size: 13px;
            color: var(--vscode-foreground, #cccccc);
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Simple Header */
        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 16px;
            background: var(--vscode-sideBar-background, #252526);
            border-bottom: 1px solid var(--vscode-panel-border, #3c3c3c);
            z-index: 10;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 600;
            font-size: 13px;
            letter-spacing: 0.5px;
            color: var(--vscode-foreground, #cccccc);
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Clean Flat Buttons */
        .btn {
            background: var(--vscode-button-background, #0e639c);
            color: var(--vscode-button-foreground, #ffffff);
            border: none;
            padding: 6px 12px;
            font-size: 12px;
            font-family: inherit;
            border-radius: 2px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: background 0.1s ease;
        }

        .btn:hover {
            background: var(--vscode-button-hoverBackground, #1177bb);
        }

        .btn-secondary {
            background: var(--vscode-button-secondaryBackground, #3a3d3e);
            color: var(--vscode-button-secondaryForeground, #ffffff);
            border: 1px solid var(--vscode-panel-border, #3c3c3c);
        }

        .btn-secondary:hover {
            background: var(--vscode-button-secondaryHoverBackground, #4f5355);
        }

        .btn-danger {
            background: #a1260d;
            color: #ffffff;
        }

        .btn-danger:hover {
            background: #cf371b;
        }

        /* Welcome / Empty View */
        #welcome-view {
            flex-grow: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
        }

        .welcome-card {
            background: var(--vscode-sideBar-background, #252526);
            border: 1px solid var(--vscode-panel-border, #3c3c3c);
            border-radius: 4px;
            padding: 32px;
            text-align: center;
            max-width: 440px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 16px;
        }

        .welcome-card h2 {
            font-size: 18px;
            font-weight: 500;
            margin: 0;
            color: var(--vscode-foreground, #cccccc);
        }

        .welcome-card p {
            color: var(--vscode-descriptionForeground, #8c8c8c);
            font-size: 12px;
            line-height: 1.5;
            margin: 0;
        }

        /* Workspace View (Full Screen Viewport) */
        #workspace-view {
            flex-grow: 1;
            display: none;
            flex-direction: column;
            position: relative;
            background-color: var(--vscode-editor-background, #1e1e1e);
            height: calc(100vh - 40px);
        }

        .viewport-toolbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 6px 16px;
            background: var(--vscode-sideBar-background, #252526);
            border-bottom: 1px solid var(--vscode-panel-border, #3c3c3c);
        }

        .image-path-info {
            font-size: 12px;
            color: var(--vscode-descriptionForeground, #8c8c8c);
            font-family: var(--vscode-editor-font-family, monospace);
        }

        .zoom-controls {
            display: flex;
            align-items: center;
            gap: 2px;
        }

        .zoom-btn {
            background: none;
            border: none;
            color: var(--vscode-foreground, #cccccc);
            cursor: pointer;
            padding: 2px 6px;
            font-size: 11px;
            border-radius: 2px;
        }

        .zoom-btn:hover {
            background: var(--vscode-toolbar-hoverBackground, rgba(255, 255, 255, 0.05));
        }

        .zoom-percent {
            font-size: 11px;
            padding: 0 4px;
            color: var(--vscode-foreground, #cccccc);
            min-width: 32px;
            text-align: center;
        }

        .canvas-area {
            flex-grow: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 16px;
            overflow: auto;
            position: relative;
            background-color: var(--vscode-editor-background, #1e1e1e);
        }

        /* Image Selection Container */
        .image-container {
            position: relative;
            display: inline-block;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            border: 1px solid var(--vscode-panel-border, #3c3c3c);
            transition: transform 0.1s ease;
        }

        .image-container img {
            display: block;
            max-width: 100%;
            max-height: 70vh;
            object-fit: contain;
            pointer-events: none;
        }

        .selection-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            cursor: crosshair;
            z-index: 10;
        }

        .selection-box {
            position: absolute;
            border: 1px dashed var(--vscode-focusBorder, #007acc);
            background: rgba(0, 122, 204, 0.15);
            display: none;
            pointer-events: none;
            z-index: 20;
        }

        /* Floating Panel Container (HUD and List side-by-side or stacked on the right) */
        .floating-container {
            position: absolute;
            top: 56px;
            right: 16px;
            width: 300px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            z-index: 100;
        }

        .hud-card {
            background: var(--vscode-sideBar-background, #252526);
            border: 1px solid var(--vscode-panel-border, #3c3c3c);
            border-radius: 3px;
            padding: 12px;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .hud-header {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--vscode-foreground, #cccccc);
            border-bottom: 1px solid var(--vscode-panel-border, #3c3c3c);
            padding-bottom: 4px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .hud-close {
            cursor: pointer;
            color: var(--vscode-descriptionForeground, #8c8c8c);
            font-size: 14px;
            line-height: 10px;
        }

        .hud-close:hover {
            color: var(--vscode-foreground, #cccccc);
        }

        .hud-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
        }

        .hud-label {
            color: var(--vscode-descriptionForeground, #8c8c8c);
        }

        .hud-val {
            font-weight: 600;
            font-family: var(--vscode-editor-font-family, monospace);
            color: var(--vscode-foreground, #cccccc);
        }

        .hsv-list-vals {
            display: flex;
            gap: 8px;
            justify-content: space-between;
            background: var(--vscode-editor-background, #1e1e1e);
            padding: 6px;
            border-radius: 2px;
            border: 1px solid var(--vscode-panel-border, #3c3c3c);
        }

        .hsv-component {
            display: flex;
            flex-direction: column;
            align-items: center;
            flex-grow: 1;
        }

        .hsv-c-label {
            font-size: 9px;
            color: var(--vscode-descriptionForeground, #8c8c8c);
            text-transform: uppercase;
        }

        .hsv-c-val {
            font-size: 13px;
            font-weight: bold;
            font-family: var(--vscode-editor-font-family, monospace);
        }

        .hsv-ranges-info {
            font-size: 11px;
            background: var(--vscode-editor-background, #1e1e1e);
            border: 1px solid var(--vscode-panel-border, #3c3c3c);
            padding: 6px;
            border-radius: 2px;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .hsv-range-box {
            font-family: var(--vscode-editor-font-family, monospace);
            word-break: break-all;
            color: #4fc1ff;
        }

        .input-group {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .text-input {
            background: var(--vscode-input-background, #3c3c3c);
            color: var(--vscode-input-foreground, #cccccc);
            border: 1px solid var(--vscode-input-border, #3c3c3c);
            padding: 4px 8px;
            font-size: 12px;
            font-family: inherit;
            border-radius: 2px;
            outline: none;
        }

        .text-input:focus {
            border-color: var(--vscode-focusBorder, #007acc);
        }

        /* Saved Ranges List */
        .ranges-manager-card {
            background: var(--vscode-sideBar-background, #252526);
            border: 1px solid var(--vscode-panel-border, #3c3c3c);
            border-radius: 3px;
            padding: 12px;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-height: 300px;
        }

        .ranges-list {
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 6px;
            max-height: 180px;
            padding-right: 4px;
        }

        .range-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--vscode-editor-background, #1e1e1e);
            border: 1px solid var(--vscode-panel-border, #3c3c3c);
            padding: 6px 8px;
            border-radius: 2px;
            font-size: 11px;
        }

        .range-item-name {
            font-weight: 600;
            color: var(--vscode-foreground, #cccccc);
        }

        .range-item-delete {
            cursor: pointer;
            color: #ef4444;
            font-size: 13px;
            font-weight: bold;
        }

        .range-item-delete:hover {
            color: #ff6b6b;
        }

        /* Simple Log Overlay (Console) */
        .logs-footer {
            background: var(--vscode-sideBar-background, #252526);
            border-top: 1px solid var(--vscode-panel-border, #3c3c3c);
            padding: 4px 16px;
            font-size: 11px;
            font-family: var(--vscode-editor-font-family, monospace);
            color: var(--vscode-descriptionForeground, #8c8c8c);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
    </style>
</head>
<body>

    <!-- Loading overlay -->
    <div class="loader-overlay" id="loading-overlay">
        <div class="loader-spinner"></div>
        <div class="loader-text" id="loader-text">Loading remote image over SSH...</div>
    </div>

    <!-- Header -->
    <header>
        <div class="brand">
            <span>SPIBERRY VISION TOOLS</span>
        </div>
        <div class="header-actions">
            <button class="btn btn-secondary" id="action-select-image-header" style="display: none;">
                Change Image
            </button>
            <button class="btn btn-secondary" id="action-reload-image" style="display: none;">
                Reload
            </button>
        </div>
    </header>

    <!-- Welcome / Empty View -->
    <main id="welcome-view">
        <div class="welcome-card">
            <h2>Vision Suite Workspace</h2>
            <p>Connect to the SpiBerry smart camera pipeline. Select remote image frames to view them, measure color average details, and generate OpenCV HSV ranges.</p>
            <button class="btn" id="action-select-image-main">
                Browse Remote Images
            </button>
        </div>
    </main>

    <!-- Workspace View -->
    <main id="workspace-view">
        
        <!-- Viewport Toolbar -->
        <div class="viewport-toolbar">
            <div class="image-path-info" id="image-info-bar">
                <span id="display-image-path">/home/pi/spiberry/captured.png</span>
            </div>
            <div class="zoom-controls">
                <button class="zoom-btn" id="btn-zoom-out">Out</button>
                <span class="zoom-percent" id="zoom-value">100%</span>
                <button class="zoom-btn" id="btn-zoom-in">In</button>
                <button class="zoom-btn" id="btn-zoom-reset" style="border-left: 1px solid var(--vscode-panel-border, #3c3c3c); padding-left: 6px;">Reset</button>
            </div>
        </div>
        
        <!-- Canvas Viewport -->
        <div class="canvas-area">
            <div class="image-container" id="img-container">
                <img id="main-image" src="" alt="SpiBerry Vision Target">
                <div class="selection-overlay" id="selection-overlay"></div>
                <div class="selection-box" id="selection-box"></div>
            </div>
        </div>

        <!-- Floating Panel Container -->
        <div class="floating-container">
            
            <!-- Floating HSV range generator HUD -->
            <div class="hud-card" id="hsv-hud" style="display: none;">
                <div class="hud-header">
                    <span>HSV Ranges Generator</span>
                    <span class="hud-close" id="hud-close-btn">&times;</span>
                </div>
                <div class="hud-row">
                    <span class="hud-label">Region Area:</span>
                    <span class="hud-val" id="hud-area-size">0 x 0 px</span>
                </div>
                <div class="hud-row">
                    <span class="hud-label">Center HSV (OpenCV):</span>
                </div>
                <div class="hsv-list-vals">
                    <div class="hsv-component">
                        <span class="hsv-c-label">H</span>
                        <span class="hsv-c-val" id="hsv-h" style="color: #4fc1ff;">0</span>
                    </div>
                    <div class="hsv-component" style="border-left: 1px solid var(--vscode-panel-border, #3c3c3c); border-right: 1px solid var(--vscode-panel-border, #3c3c3c);">
                        <span class="hsv-c-label">S</span>
                        <span class="hsv-c-val" id="hsv-s" style="color: #4fc1ff;">0</span>
                    </div>
                    <div class="hsv-component">
                        <span class="hsv-c-label">V</span>
                        <span class="hsv-c-val" id="hsv-v" style="color: #4fc1ff;">0</span>
                    </div>
                </div>

                <div class="hud-row" style="margin-top: 4px;">
                    <span class="hud-label">Generated Bounds (Offset ±10, ±55, ±55):</span>
                </div>
                <div class="hsv-ranges-info">
                    <div class="hsv-range-box" id="hsv-bounds-display">[[0,0,0],[0,0,0]]</div>
                </div>

                <div class="input-group">
                    <label class="hud-label" for="color-name-input">Color Name:</label>
                    <input type="text" class="text-input" id="color-name-input" placeholder="e.g. red_box, green_dot">
                </div>

                <button class="btn" id="hud-save-btn" style="justify-content: center;">
                    Save Color Range
                </button>
            </div>

            <!-- Saved Color Ranges list Manager -->
            <div class="ranges-manager-card" id="ranges-manager">
                <div class="hud-header">
                    <span>Saved Ranges</span>
                </div>
                <div class="ranges-list" id="ranges-list-container">
                    <!-- Dynamic range items -->
                    <div class="hud-label" style="text-align: center; padding: 12px 0;" id="empty-ranges-message">No ranges saved yet.</div>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button class="btn" id="copy-all-btn" style="flex-grow: 1; justify-content: center; font-size: 11px; padding: 4px;">
                        Copy Ranges JSON
                    </button>
                    <button class="btn btn-secondary btn-danger" id="clear-all-btn" style="font-size: 11px; padding: 4px;">
                        Clear
                    </button>
                </div>
            </div>

        </div>

        <!-- Minimal Footer log -->
        <div class="logs-footer">
            <span id="footer-status-text">Vision pipeline standing by. Click and drag on the image to select a region.</span>
        </div>

    </main>

    <script nonce="${nonce}">
        const vscodeApi = acquireVsCodeApi();

        const welcomeView = document.getElementById('welcome-view');
        const workspaceView = document.getElementById('workspace-view');
        const selectImageMainBtn = document.getElementById('action-select-image-main');
        const selectImageHeaderBtn = document.getElementById('action-select-image-header');
        const reloadImageBtn = document.getElementById('action-reload-image');
        const loadingOverlay = document.getElementById('loading-overlay');
        const loaderText = document.getElementById('loader-text');

        // Viewport Canvas Elements
        const mainImage = document.getElementById('main-image');
        const displayImagePath = document.getElementById('display-image-path');
        const imgContainer = document.getElementById('img-container');
        const selectionOverlay = document.getElementById('selection-overlay');
        const selectionBox = document.getElementById('selection-box');
        const footerStatusText = document.getElementById('footer-status-text');

        // Zoom Elements
        const zoomValue = document.getElementById('zoom-value');
        const btnZoomIn = document.getElementById('btn-zoom-in');
        const btnZoomOut = document.getElementById('btn-zoom-out');
        const btnZoomReset = document.getElementById('btn-zoom-reset');

        // HUD & Range Elements
        const hsvHud = document.getElementById('hsv-hud');
        const hudAreaSize = document.getElementById('hud-area-size');
        const hudCloseBtn = document.getElementById('hud-close-btn');
        const hsvHVal = document.getElementById('hsv-h');
        const hsvSVal = document.getElementById('hsv-s');
        const hsvVVal = document.getElementById('hsv-v');
        const hsvBoundsDisplay = document.getElementById('hsv-bounds-display');
        const colorNameInput = document.getElementById('color-name-input');
        const hudSaveBtn = document.getElementById('hud-save-btn');

        // Manager Elements
        const rangesListContainer = document.getElementById('ranges-list-container');
        const emptyRangesMessage = document.getElementById('empty-ranges-message');
        const copyAllBtn = document.getElementById('copy-all-btn');
        const clearAllBtn = document.getElementById('clear-all-btn');

        let currentImagePath = '';
        let currentZoom = 100;
        let isDragging = false;
        let startX = 0;
        let startY = 0;

        // HSV ranges storage
        // Format: { "color_name": [ [lower1, upper1], [lower2, upper2] ] }
        let savedRanges = {};

        // Active calculated parameters
        let calculatedCenter = [0, 0, 0];
        let calculatedRanges = [];

        // Constants
        const HSV_OFFSET = [10, 55, 55];

        // Hidden canvas for pixel extraction
        const hiddenCanvas = document.createElement('canvas');
        const hiddenCtx = hiddenCanvas.getContext('2d');

        // Update footer log status
        function updateStatus(text) {
            footerStatusText.textContent = text;
        }

        // Image Load Handling
        mainImage.onload = () => {
            hiddenCanvas.width = mainImage.naturalWidth;
            hiddenCanvas.height = mainImage.naturalHeight;
            hiddenCtx.drawImage(mainImage, 0, 0);
            updateStatus('Loaded remote image: ' + mainImage.naturalWidth + 'x' + mainImage.naturalHeight + ' pixels.');
            
            // Hide selection elements on reload
            selectionBox.style.display = 'none';
            hsvHud.style.display = 'none';
        };

        // Zoom Management
        function applyZoom() {
            imgContainer.style.transform = 'scale(' + (currentZoom / 100) + ')';
            zoomValue.textContent = currentZoom + '%';
        }

        btnZoomIn.addEventListener('click', () => {
            if (currentZoom < 400) {
                currentZoom += 25;
                applyZoom();
            }
        });

        btnZoomOut.addEventListener('click', () => {
            if (currentZoom > 25) {
                currentZoom -= 25;
                applyZoom();
            }
        });

        btnZoomReset.addEventListener('click', () => {
            currentZoom = 100;
            applyZoom();
        });

        // Mouse Drag Region Selection
        selectionOverlay.addEventListener('mousedown', (e) => {
            isDragging = true;
            startX = e.offsetX;
            startY = e.offsetY;

            selectionBox.style.left = startX + 'px';
            selectionBox.style.top = startY + 'px';
            selectionBox.style.width = '0px';
            selectionBox.style.height = '0px';
            selectionBox.style.display = 'block';
            hsvHud.style.display = 'none';
        });

        selectionOverlay.addEventListener('mousemove', (e) => {
            if (!isDragging) return;

            const currentX = Math.max(0, Math.min(selectionOverlay.clientWidth, e.offsetX));
            const currentY = Math.max(0, Math.min(selectionOverlay.clientHeight, e.offsetY));

            const x = Math.min(startX, currentX);
            const y = Math.min(startY, currentY);
            const w = Math.abs(startX - currentX);
            const h = Math.abs(startY - currentY);

            selectionBox.style.left = x + 'px';
            selectionBox.style.top = y + 'px';
            selectionBox.style.width = w + 'px';
            selectionBox.style.height = h + 'px';
        });

        const finishSelection = (e) => {
            if (!isDragging) return;
            isDragging = false;

            const boxLeft = parseInt(selectionBox.style.left) || 0;
            const boxTop = parseInt(selectionBox.style.top) || 0;
            const boxWidth = parseInt(selectionBox.style.width) || 0;
            const boxHeight = parseInt(selectionBox.style.height) || 0;

            if (boxWidth < 2 || boxHeight < 2) {
                selectionBox.style.display = 'none';
                hsvHud.style.display = 'none';
                return;
            }

            calculateHsvAndRanges(boxLeft, boxTop, boxWidth, boxHeight);
        };

        selectionOverlay.addEventListener('mouseup', finishSelection);
        selectionOverlay.addEventListener('mouseleave', finishSelection);

        hudCloseBtn.addEventListener('click', () => {
            hsvHud.style.display = 'none';
            selectionBox.style.display = 'none';
        });

        // Save Color Action
        hudSaveBtn.addEventListener('click', () => {
            const rawName = colorNameInput.value.trim();
            if (!rawName) {
                updateStatus('Error: Please enter a color name before saving.');
                return;
            }

            const cleanName = rawName.toLowerCase().replace(/[^a-z0-9_-]/g, '_');
            
            // Save the calculated ranges
            savedRanges[cleanName] = calculatedRanges;
            
            colorNameInput.value = '';
            hsvHud.style.display = 'none';
            selectionBox.style.display = 'none';

            updateStatus('Saved color range: "' + cleanName + '"');
            renderSavedRanges();
        });

        // Copy JSON representation
        copyAllBtn.addEventListener('click', () => {
            const jsonText = JSON.stringify(savedRanges);
            
            const tempTextArea = document.createElement('textarea');
            tempTextArea.value = jsonText;
            document.body.appendChild(tempTextArea);
            tempTextArea.select();
            document.execCommand('copy');
            document.body.removeChild(tempTextArea);
            
            updateStatus('Copied saved color ranges JSON to clipboard.');
            vscodeApi.postMessage({ command: 'info', message: 'Color ranges JSON copied to clipboard!' });
        });

        // Clear All Action
        clearAllBtn.addEventListener('click', () => {
            savedRanges = {};
            renderSavedRanges();
            updateStatus('Cleared all saved color ranges.');
        });

        // Render Saved ranges list helper
        function renderSavedRanges() {
            // Clear prior dynamic lists
            const items = rangesListContainer.querySelectorAll('.range-item');
            items.forEach(el => el.remove());

            const keys = Object.keys(savedRanges);
            if (keys.length === 0) {
                emptyRangesMessage.style.display = 'block';
                return;
            }

            emptyRangesMessage.style.display = 'none';

            keys.forEach(name => {
                const item = document.createElement('div');
                item.className = 'range-item';

                const nameSpan = document.createElement('span');
                nameSpan.className = 'range-item-name';
                nameSpan.textContent = name;

                const detailSpan = document.createElement('span');
                detailSpan.style.color = 'var(--vscode-descriptionForeground)';
                detailSpan.style.fontSize = '9px';
                detailSpan.style.fontFamily = 'monospace';
                // Show bounds summary
                const count = savedRanges[name].length;
                detailSpan.textContent = count === 2 ? '2 bounds (wraps)' : '1 bound';

                const deleteSpan = document.createElement('span');
                deleteSpan.className = 'range-item-delete';
                deleteSpan.innerHTML = '&times;';
                deleteSpan.title = 'Delete range';
                deleteSpan.addEventListener('click', () => {
                    delete savedRanges[name];
                    renderSavedRanges();
                    updateStatus('Deleted color range: "' + name + '"');
                });

                item.appendChild(nameSpan);
                item.appendChild(detailSpan);
                item.appendChild(deleteSpan);
                rangesListContainer.appendChild(item);
            });
        }

        // HSV Calculations using Circular mean for Hue & generate HSV offset bounds
        function calculateHsvAndRanges(x, y, w, h) {
            const dispW = selectionOverlay.clientWidth;
            const dispH = selectionOverlay.clientHeight;
            const natW = mainImage.naturalWidth;
            const natH = mainImage.naturalHeight;

            if (!natW || !natH) return;

            const scaleX = natW / dispW;
            const scaleY = natH / dispH;

            // Map box to native dimensions
            const nx = Math.max(0, Math.min(natW - 1, Math.floor(x * scaleX)));
            const ny = Math.max(0, Math.min(natH - 1, Math.floor(y * scaleY)));
            let nw = Math.max(1, Math.floor(w * scaleX));
            let nh = Math.max(1, Math.floor(h * scaleY));

            if (nx + nw > natW) nw = natW - nx;
            if (ny + nh > natH) nh = natH - ny;

            try {
                const imgData = hiddenCtx.getImageData(nx, ny, nw, nh);
                const data = imgData.data;

                // Hue circular mean: sum of sine and cosine component angles
                let sumCos = 0;
                let sumSin = 0;
                let sumS = 0;
                let sumV = 0;
                let pixelCount = 0;

                for (let i = 0; i < data.length; i += 4) {
                    const r = data[i];
                    const g = data[i+1];
                    const b = data[i+2];

                    // Convert RGB values to HSV
                    const rf = r / 255;
                    const gf = g / 255;
                    const bf = b / 255;

                    const max = Math.max(rf, gf, bf);
                    const min = Math.min(rf, gf, bf);
                    const delta = max - min;

                    let hDeg = 0;
                    let sFrac = 0;
                    const vFrac = max;

                    if (delta > 0) {
                        sFrac = delta / max;
                        if (max === rf) {
                            hDeg = ((gf - bf) / delta) % 6;
                        } else if (max === gf) {
                            hDeg = (bf - rf) / delta + 2;
                        } else {
                            hDeg = (rf - gf) / delta + 4;
                        }
                        hDeg *= 60;
                        if (hDeg < 0) hDeg += 360;
                    } else {
                        sFrac = 0;
                        hDeg = 0;
                    }

                    // Convert to OpenCV HSV standard
                    const opencvH = hDeg / 2; // Keep float for angle averaging
                    const opencvS = Math.round(sFrac * 255);
                    const opencvV = Math.round(vFrac * 255);

                    // Hue OpenCV H: 0–179 wraps. Map 0-179 to 0-360 deg in radians.
                    const angleRad = (opencvH * 2.0) * Math.PI / 180;
                    sumCos += Math.cos(angleRad);
                    sumSin += Math.sin(angleRad);

                    sumS += opencvS;
                    sumV += opencvV;
                    pixelCount++;
                }

                if (pixelCount > 0) {
                    // Compute circular mean angle for H
                    const avgCos = sumCos / pixelCount;
                    const avgSin = sumSin / pixelCount;
                    let avgAngle = Math.atan2(avgSin, avgCos);
                    if (avgAngle < 0) {
                        avgAngle += 2 * Math.PI;
                    }
                    // Map back to 0-179 OpenCV Hue range
                    const avgH = Math.round((avgAngle * 180 / Math.PI) / 2.0) % 180;

                    // Standard arithmetic averages for S & V
                    const avgS = Math.round(sumS / pixelCount);
                    const avgV = Math.round(sumV / pixelCount);

                    calculatedCenter = [avgH, avgS, avgV];

                    // Generate bounds with offset ±10, ±55, ±55
                    calculatedRanges = generateHsvRanges(calculatedCenter, HSV_OFFSET);

                    // Update UI elements
                    hudAreaSize.textContent = nw + ' x ' + nh + ' px (native)';
                    hsvHVal.textContent = avgH;
                    hsvSVal.textContent = avgS;
                    hsvVVal.textContent = avgV;

                    hsvBoundsDisplay.textContent = JSON.stringify(calculatedRanges);
                    hsvHud.style.display = 'flex';

                    updateStatus('Calculated HSV center: [' + avgH + ', ' + avgS + ', ' + avgV + ']');
                }
            } catch (err) {
                updateStatus('Calculation error: ' + err.message);
            }
        }

        // HSV Range Bound Offset Generator (handles low/high wrapping on Hue)
        function generateHsvRanges(center, offset) {
            const h = center[0];
            const s = center[1];
            const v = center[2];
            const h_off = offset[0];
            const s_off = offset[1];
            const v_off = offset[2];

            const lower = [h - h_off, Math.max(s - s_off, 0), Math.max(v - v_off, 0)];
            const upper = [h + h_off, Math.min(s + s_off, 255), Math.min(v + v_off, 255)];

            const ranges = [];
            if (lower[0] < 0) {
                // H wraps low: range 1 from [0, s_min, v_min] to [upper_h, s_max, v_max]
                ranges.push([
                    [0, lower[1], lower[2]],
                    [upper[0], upper[1], upper[2]]
                ]);
                // range 2 from [180+lower_h, s_min, v_min] to [179, s_max, v_max]
                const wrap_low = 180 + lower[0];
                ranges.push([
                    [wrap_low, lower[1], lower[2]],
                    [179, upper[1], upper[2]]
                ]);
            } else if (upper[0] > 179) {
                // H wraps high: range 1 from [0, s_min, v_min] to [upper_h-180, s_max, v_max]
                const wrap_high = upper[0] - 180;
                ranges.push([
                    [0, lower[1], lower[2]],
                    [wrap_high, upper[1], upper[2]]
                ]);
                // range 2 from [lower_h, s_min, v_min] to [179, s_max, v_max]
                ranges.push([
                    [lower[0], lower[1], lower[2]],
                    [179, upper[1], upper[2]]
                ]);
            } else {
                ranges.push([lower, upper]);
            }
            return ranges;
        }

        // Image selection action buttons
        function requestImageSelection() {
            vscodeApi.postMessage({ command: 'pick-image' });
        }

        selectImageMainBtn.addEventListener('click', requestImageSelection);
        selectImageHeaderBtn.addEventListener('click', requestImageSelection);

        reloadImageBtn.addEventListener('click', () => {
            if (currentImagePath) {
                vscodeApi.postMessage({ command: 'reload-image', path: currentImagePath });
            }
        });

        // Messages from Extension Back-end
        window.addEventListener('message', event => {
            const message = event.data;
            switch (message.type) {
                case 'show-image':
                    currentImagePath = message.data.path;
                    displayImagePath.textContent = message.data.path;
                    mainImage.src = message.data.dataUri;
                    
                    // Switch viewports
                    welcomeView.style.display = 'none';
                    workspaceView.style.display = 'flex';
                    
                    // Show actions
                    selectImageHeaderBtn.style.display = 'flex';
                    reloadImageBtn.style.display = 'flex';

                    // Reset zoom level
                    currentZoom = 100;
                    applyZoom();
                    break;

                case 'loading':
                    loaderText.textContent = message.text || 'Retrieving remote asset...';
                    loadingOverlay.style.display = 'flex';
                    break;

                case 'loading-finished':
                    loadingOverlay.style.display = 'none';
                    break;

                case 'error':
                    updateStatus('Error: ' + message.message);
                    break;
            }
        });
    </script>
</body>
</html>`;
}
