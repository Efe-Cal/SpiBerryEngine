# SpiBerryEngine

A project that aims to primarily control LEGO SPIKE with a Raspberry Pi.
It uses the `mpremote` tool to communicate with the LEGO SPIKE hub.

See [this Youtube video](https://youtu.be/eZQZYIM7QZc) for an introduction and demonstration of the project.

## Installation

### Recommended: Installing via PyPI

The simplest way to install SpiBerryEngine is from PyPI:

```bash
pip install spiberry-engine
```

For vision support (OpenCV/Ultralytics) and camera features:

```bash
pip install "spiberry-engine[full]"
```

Other extras:
- `spiberry-engine[vision]` - Vision features (OpenCV/Ultralytics)
- `spiberry-engine[camera]` - Camera capture features
- `spiberry-engine[controller]` - Remote drive controller features

After installation, initialize your environment (creates config and default robot code):

```bash
spiberry init
```

### Alternative: Using the Engine Standalone

Transfer the `spiberry.pyz` file to your Raspberry Pi and run it:
```bash
python spiberry.pyz
```
It will create a virtual environment and install dependencies. Service installation is explicit via the `--install-service` flag. 

Install and optionally start the service from the installer flow:

```bash
sudo python spiberry.pyz --install-service --start-service
```

## Hardware Setup

Connect the following components to your Raspberry Pi:

- **Starter Pin**: Must be connected to ground (GPIO 21 by default) to start the program. You can bypass this by setting the environment variable `IGNORE_STARTER_PIN=1`.
- **RGB LED**: Connect to the GPIO pins specified during initialization or defaults:
  - Red: GPIO 0
  - Green: GPIO 11
  - Blue: GPIO 9
You can disable the RGB LED by setting `rgb_led_enabled = False` under `[GPIO]` in the config file.
- **Button**: Connect to GPIO pin specified (default: 17)

## Usage

### CLI Commands

When installed via PyPI, several commands are available:

| Command | Description |
|---------|-------------|
| `spiberry init` | Initialize default config and robot code |
| `spiberry run-engine` | Run the main engine |
| `spiberry-start` | Start the systemd service |
| `spiberry-stop` | Stop the systemd service |
| `spiberry-status` | Check service status |
| `spiberry-remote-drive` | Start remote drive controller |

### Running the Engine

To run the engine manually with the default configuration:
```bash
spiberry run-engine
```

You can also specify a custom robot code file:
```bash
spiberry run-engine my_cool_robot.py
```

### Configuration File

SpiBerryEngine stores runtime settings in:

```text
~/spiberry_config.ini
```

On first run or with the `spiberry init` command, this file is created automatically with defaults similar to:

```ini
[GPIO]
red = 0
green = 11
blue = 9
button = 17
active_high = False

[Code]
path = robot_code.py
raspi_functions_path = raspi_functions/
trigger_mode = external # Options: external, builtin

[Vision]
enabled = False

[Camera]
take_picture_method = picamera2
timeout = 0
width = 1920
height = 1080

[RemoteDrive]
left_motor = port.A
right_motor = port.B
```

Notes:

- `Code.path` controls which robot code file is executed.
- `Code.raspi_functions_path` can point to either:
  - a Python file (for example `raspi_functions.py`), or
  - a package directory (for example `raspi_functions/`, using `__init__.py`).
- Vision features are only loaded when `Vision.enabled = True`.
- `RemoteDrive.left_motor` and `RemoteDrive.right_motor` set default motor ports for remote drive mode.

CLI GPIO pin arguments are now persisted into the config file when provided:

```bash
# Example if running standalone
python spiberry.pyz --red 0 --green 11 --blue 9 --button 17
```

The values are then saved under `[GPIO]`.

## Deployment & Extension

Note: See [the VS Code Extension](extension/spiberry/README.md) for easier installation and code deployment. The extension provides a user-friendly interface, and is recommended.

### Deploying Code
Recommended method: Use the [VS Code Extension](extension/spiberry/README.md)  

Use [deploy_robot_code.py](deploy_robot_code.py) to deploy your robot code:

1. Run the deploy tool on your computer
2. Select your `.llsp3` file (LEGO SPIKE project export)
3. Optionally select a Raspi Functions file (see below)
4. Enter your Raspberry Pi connection details
5. Click "Deploy" or use the hotkey `Ctrl+Shift+D`

The deployer will:
- Extract your code from the `.llsp3` file
- Send `robot_code.py` to your Raspberry Pi
- Optionally send `raspi_functions.py` if provided
- Save your configuration for future deployments

### Using Raspi Utility Classes

Copy the contents of [raspi-util-class.py](extension/spiberry/raspi-util-class.py) and paste it at the top of your robot code. This provides easy-to-use classes for interacting with Raspberry Pi hardware from your LEGO SPIKE code.

#### Example Usage

```python
# Copy raspi-util-class.py contents here at the top of your code

# Create Raspi instance
raspi = Raspi()

# Register devices
servo = raspi.register_device("servo", "s1", "14","0","180","0.00095","0.0028","10")
# Parameters are: type, name, pin, min_angle, max_angle, min_pulse, max_pulse, start_angle
distance_sensor = raspi.register_device("distance_sensor", "my_sensor", "15", "16", "4")
# Parameters are: type, name, trigger_pin, echo_pin, max_distance_m

# Use devices
servo.set_angle(90)
current_angle = servo.get_angle()
distance = distance_sensor.get_distance()

# Call custom functions (if you have raspi_functions.py)
result = raspi.my_custom_function() # Preferred way to call custom functions
result = raspi.func("some_custom_function()") # Deprecated, may be removed in future versions
```

The utility classes support:
- **Servo**: `set_angle(angle)`, `get_angle()`
- **Distance Sensor**: `get_distance()`
- **Custom Functions**: `raspi.my_custom_function()` to call functions from your `raspi_functions.py`

## RGBLED Signals

The RGB LED provides visual feedback for the system state:

| Color      | Meaning                                 |
|------------|-----------------------------------------|
| Red        | Connection error or module not found    |
| Green      | Ready/Idle/Success                      |
| Blue       | Run Error                               |
| Yellow     | Work starting                           |
| Cyan       | Code or functions reloaded              |

### Blinking Patterns

| Color | Blink Count | Blink Duration | Meaning                                 |
|-------|-------------|---------------|-----------------------------------------|
| Red   | 2           | 0.2s          | `raspi_functions` import error          |
| Red   | 2           | 0.2s          | Stopped code execution                  |
| Red   | 5           | 0.1s          | `mpremote` not found                    |
| Red   | 5           | 0.3s          | Connection error                        |
| Blue  | 2           | 0.1s          | REPL error                              |
| Blue  | 2           | 0.3s          | Function call function not found error  |
| Blue  | 5           | 0.1s          | Code execution error                    |
| Green | 2           | 0.2s          | Code started/stopped/ended              |
| Cyan  | 2           | 0.2s          | Code reloaded                           |
| Cyan  | 3           | 0.2s          | Functions reloaded                      |
| Cyan  | 5           | 0.2s          | Functions & Code reloaded               |

## Camera Configuration

SpiBerryEngine supports two camera capture methods: `picamera2` (recommended for Raspberry Pi OS) and `rpicam-still` (command-line tool). Both methods support comprehensive configuration options.

#### Configuration Options Reference

See [examples/camera_config_examples.py](examples/camera_config_examples.py) for comprehensive examples and the [picamera2 manual](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf) and [rpicam-still documentation](https://www.raspberrypi.com/documentation/computers/camera_software.html) for complete option lists.

## Vision Processing
SpiBerryEngine includes a `Vision` and `ContourDetector` classes that provides some image processing capabilities using OpenCV and object detection using Ultralytics. You can use the `take_picture()` method to capture an image and then apply various processing methods like `detect_objects()`, `find_contours()`, or custom OpenCV operations.   
See [examples/vision_examples.py](examples/vision_examples.py) for usage examples.


## Files Overview

- [`main.py`](spiberry/app/main.py) - Main engine script
- [`vision.py`](spiberry/app/vision.py) - Vision processing classes (Vision, ContourDetector)
- [`camera.py`](spiberry/app/camera.py) - Camera capture classes
- [`remote_drive/`](spiberry/remote_drive/) - Remote drive control module (client and controller)
- [`installer.py`](installer.py) - (deprecated) Installation script with GUI
- [`deploy_robot_code.py`](deploy_robot_code.py) - (deprecated) Code deployment tool with GUI
- [`sbe.service`](spiberry/sbe.service) - Systemd service configuration
- [`requirements.txt`](requirements.txt) - Python dependencies
- [`scripts/`](spiberry/scripts/) - Helper scripts for service management

## Connections and Hardware
- Raspberry Pi GPIO pins for RGB LED and Button
- LEGO SPIKE Hub connected via USB to Raspberry Pi
- Raspberry Pi running Raspberry Pi OS with Python 3

## Troubleshooting
- Check the RGB LED signals for error codes
- Ensure all dependencies are installed
- Ensure there is no syntax error in your robot code (Spike App does not always show them)
- Check your installation and code deployment paths

## Disclaimer
This project is an independent community project and is not affiliated with, endorsed by, or sponsored by LEGO Group or Raspberry Pi Ltd.
Use at your own risk. Always follow safety guidelines when working with hardware.