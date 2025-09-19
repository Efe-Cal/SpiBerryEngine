# SpiBerryEngine

A project that aims to primarily control Lego Spike with a Raspberry Pi.
It uses the `mpremote` tool to communicate with the Lego Spike hub.
I believe it can also be used with other micropython devices.

## Installation

### Installing the Engine

Use the [installer.exe](installer.exe) (compiled from [installer.py](installer.py)) to install SpiBerryEngine on your Raspberry Pi:

1. Run the installer on your computer
2. Enter your Raspberry Pi connection details:
   - Remote Host (default: `raspberrypi`)
   - Remote User (default: `pi`)
   - Password
   - Remote Directory (where to install)
3. Configure GPIO pins for hardware:
   - R pin (Red LED, default: 0)
   - B pin (Blue LED, default: 11) 
   - G pin (Green LED, default: 9)
   - Button pin (default: 17)
4. Click "Start Installation"

The installer will:
- Download and package all dependencies (make sure the dependencies archive is in the same folder as the installer)
- Transfer files to your Raspberry Pi via SSH
- Set up a Python virtual environment
- Install all required packages
- Create a `run.sh` script with your GPIO configuration

### Installing as a System Service

To run SpiBerryEngine automatically on boot, install it as a systemd service using [sbe.service](sbe.service):
(Change the `User`, `WorkingDirectory`, and `ExecStart` paths as needed.)
```bash
# Copy the service file to systemd
sudo cp sbe.service /etc/systemd/system/

# Reload systemd and enable the service
sudo systemctl daemon-reload
sudo systemctl enable sbe.service

# Start the service
sudo systemctl start sbe.service

# Check service status
sudo systemctl status sbe.service
```

The service will:
- Start automatically on boot
- Restart on failure
- Run as the `pi` user
- Log output to the system journal

## Hardware Setup

Connect the following components to your Raspberry Pi:

- **RGB LED**: Connect to the GPIO pins specified during installation or defaults:
  - Red: GPIO 0
  - Green: GPIO 11
  - Blue: GPIO 9
- **Button**: Connect to GPIO pin specified (default: 17)

## Usage

### Running Manually

```bash
cd /home/pi/ro  # or your installation directory
./run.sh
```

Or with custom GPIO pins:
```bash
python SpiBerryEngine.py --button 11 --red 22 --green 10 --blue 9
```

### Deploying Code

Use [deploy_robot_code.exe](deploy_robot_code.exe) (compiled from [deploy_robot_code.py](deploy_robot_code.py)) to deploy your robot code:

1. Run the deploy tool on your computer
2. Select your `.llsp3` file (Lego Spike project export)
3. Optionally select a Raspi Functions file (see below)
4. Enter your Raspberry Pi connection details
5. Click "Deploy" or use the hotkey `Ctrl+Shift+D`

The deployer will:
- Extract your code from the `.llsp3` file
- Send `robot_code.py` to your Raspberry Pi
- Optionally send `raspi_functions.py` if provided
- Save your configuration for future deployments

### Using Raspi Utility Classes

Copy the contents of [raspi-util-class.py](raspi-util-class.py) and paste it at the top of your robot code. This provides easy-to-use classes for interacting with Raspberry Pi hardware from your Lego Spike code.

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
result = raspi.func("some_custom_function()")
```

The utility classes support:
- **Servo**: `set_angle(angle)`, `get_angle()`
- **Distance Sensor**: `get_distance()`
- **Custom Functions**: `raspi.func("function_call()")` to call functions from your `raspi_functions.py`

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

## Files Overview

- [`SpiBerryEngine.py`](SpiBerryEngine.py) - Main engine script
- [`installer.py`](installer.py) - Installation script with GUI
- [`deploy_robot_code.py`](deploy_robot_code.py) - Code deployment tool with GUI
- [`raspi-util-class.py`](raspi-util-class.py) - Utility classes for robot code
- [`sbe.service`](sbe.service) - Systemd service configuration
- [`requirements.txt`](requirements.txt) - Python dependencies

## Connections and Hardware
- Raspberry Pi GPIO pins for RGB LED and Button
- Lego Spike Hub connected via USB to Raspberry Pi
- Raspberry Pi running Raspberry Pi OS with Python 3

## Troubleshooting
- Chect the RGB LED signals for error codes
- Ensure all dependencies are installed
- Ensure there is no syntax error in your robot code (Spike App does not always show them)
- Check your instalation and code deployment paths