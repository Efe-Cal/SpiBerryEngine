# SpiBerryEngine

A project that aims to primarily control Lego Spike with a Raspberry Pi.
It uses the `mpremote` tool to communicate with the Lego Spike hub.
I believe it can also be used with other micropython devices 

## Setup

- Connect an RGB LED to the GPIO pins specified in the arguments or defaults:
  - Red: GPIO 22
  - Green: GPIO 10
  - Blue: GPIO 9
- Connect a button to the GPIO pin specified (default: 11).

## Running

```sh
python SpiBerryEngine.py
```

You can override pin assignments with command-line arguments:
```sh
python SpiBerryEngine.py --button 11 --red 22 --green 10 --blue 9
```

## RGBLED Signals

The RGB LED provides visual feedback for the system state:

| Color      | Meaning                                 |
|------------|-----------------------------------------|
| Red        | Connection error or module not found    |
| Green      | Ready/Idle/Success                      |
| Blue       | Run Error                               |
| Yellow     | Work starting                           |
| Cyan       | Code or functions reloaded              |

### Blinking
| Color | Blink Count | Blink Duration | Meaning                                 |
|-------|-------------|---------------|-----------------------------------------|
| Red   | 2           | 0.2s          | `raspi_functions` import error          |
| Red   | 2           | 0.2           | Stopped code execution
| Red   | 5           | 0.1s          | `mpremote` not found                    |
| Red   | 5           | 0.3s          | Connection error                        |
| Blue  | 2           | 0.1s          | REPL error                              |
| Blue  | 2           | 0.3s          | Function call function not found error  |
| Blue  | 5           | 0.1s          | Code execution error                    |
| Green | 2           | 0.2s          | Code started/stopped/ended              |
| Cyan  | 2           | 0.2s          | Code reloaded                           |
| Cyan  | 3           | 0.2s          | Functions reloaded                      |
| Cyan  | 5           | 0.2s          | Functions & Code reloaded               |