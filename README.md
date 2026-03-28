# SpiBerryEngine

A project that aims to primarily control LEGO SPIKE with a Raspberry Pi.
It uses the `mpremote` tool to communicate with the LEGO SPIKE hub.
I believe it can also be used with other micropython devices.

Note: See [the VS Code Extension](extension/spiberry/README.md) for easier installation and code deployment. The methods described in this README are still supported but the extension provides a more user-friendly interface.

## Installation

### Installing the Engine

Transfer the `spiberry.pyz` file to your Raspberry Pi and run it:
```bash
python spiberry.pyz
```
It will create a virtual environment, install dependencies and setup a system service to run the engine on boot. You can also specify GPIO pins for the RGB LED and button during installation or later using the `--set-pins` option.

## Hardware Setup

Connect the following components to your Raspberry Pi:

- **Starter Pin**: Must be connected to ground (GPIO 21) to start the program. You can bypass this by setting the environment variable `IGNORE_STARTER_PIN=1`.
- **RGB LED**: Connect to the GPIO pins specified during installation or defaults:
  - Red: GPIO 0
  - Green: GPIO 11
  - Blue: GPIO 9
- **Button**: Connect to GPIO pin specified (default: 17)

## Usage

### Running Manually

To run the engine manually, execute the following command on your Raspberry Pi, and optionally specify the GPIO pins for the RGB LED and button:
```bash
python spiberry.pyz --blue 11 --button 22
```

Alternatively, you can use `--set-pins` to interactively configure pins during or after installation:
```bash
python spiberry.pyz --set-pins
```

### Deploying Code

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