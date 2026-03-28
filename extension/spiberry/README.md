# SpiBerry VS Code Extension

A VS Code extension for developing and deploying Python code to LEGO Spike robots running on Raspberry Pi via the SpiBerryEngine.

## Features

- **Control Panel**: Built-in UI for monitoring and controlling your device
- **Device Connectivity Status**: Visual status bar indicator showing if your Raspberry Pi device is reachable
- **SSH Connection Management**: Securely store and manage SSH credentials for your device
- **Interactive SSH Console**: Open an interactive terminal session with your device easily from VS Code
- **One-Click Code Deployment**: Send your Python code to the remote device with a single command
- **Auto-Send on Save**: Automatically deploy code when you save your file (configurable)
- **SpiBerryEngine Installation**: Install the latest SpiBerryEngine directly from GitHub releases
- **Service Management**: Enable, disable, start, and stop the SpiBerryEngine service
- **Service Logs**: Follow the service journal logs in real-time
- **LEGO Spike Python Typings**: Install type hints for LEGO Spike Prime Python v3 API
- **Raspi Utility Classes**: Insert utility classes for easier Raspberry Pi usage in your code

## Requirements

- A Raspberry Pi
- Network connectivity between your development machine and the Raspberry Pi (see [this guide](https://gist.github.com/Efe-Cal/03c9f99aca4c5aefcd035b2f5d556977) for easy setup)

## Quick Start

1. **Set Device Credentials**
   - Run `SpiBerry: Set Device Credentials` from the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
   - Enter the IP address/hostname, username, and password when prompted

2. **Install SpiBerryEngine** (first time only)
   - Run `SpiBerry: Install SpiBerryEngine` from the Command Palette
   - This downloads and installs the engine on your device

3. **Install Python Typings** (optional but recommended)
   - Run `SpiBerry: Install Typings` from the Command Palette
   - Choose Workspace (recommended) or Global installation

4. **Deploy Your Code**
   - Open a Python file in the editor
   - Run `SpiBerry: Send Code to Device`, or
   - Enable auto-send on save in settings and simply save your file

## Commands

| Command | Description |
|---------|-------------|
| `spiberry.setDeviceCredentials` | Configure SSH connection details |
| `spiberry.sendCodeToDevice` | Send current file to the device |
| `spiberry.installSpiBerryEngine` | Download and install SpiBerryEngine |
| `spiberry.installTypings` | Install LEGO Spike Python type hints |
| `spiberry.enableService` | Enable the SpiBerryEngine service |
| `spiberry.disableService` | Disable the SpiBerryEngine service |
| `spiberry.startService` | Start the SpiBerryEngine service |
| `spiberry.stopService` | Stop the SpiBerryEngine service |
| `spiberry.insertRaspiUtilClasses` | Insert the Raspi utility class into the current file |
| `spiberry.openSshConsole` | Open an interactive SSH console |
| `spiberry.followServiceJournal` | Follow the SpiBerryEngine service journal logs |

## Extension Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `spiberry.autoSendOnSave` | `false` | Automatically send code when saving |
