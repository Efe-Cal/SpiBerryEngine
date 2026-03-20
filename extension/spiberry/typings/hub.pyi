from typing import Any, Awaitable, Callable, Iterable, List, Optional, Tuple, Union

"""The hub module contains functions to get information from the LEGO Hub itself."""
@staticmethod
def device_uuid() -> str:
    """Retrieve the device UUID."""
    ...
@staticmethod
def hardware_id() -> str:
    """Retrieve the hardware ID."""
    ...
@staticmethod
def power_off() -> int:
    """Turns off the hub."""
    ...
@staticmethod
def temperature() -> int:
    """Retrieve the hub temperature in decidegrees Celsius (1/10 degree)."""
    ...

class button:
    """Module to react to buttons being pressed on the hub."""
    LEFT: int = 1
    RIGHT: int = 2
    @staticmethod
    def pressed(button: int) -> int:
        """Check how long a button has been pressed.
        
        Args:
            button: A button from the button submodule (LEFT/RIGHT).
        
        Returns:
            Duration in milliseconds.
        """
        ...

class light:
    """Module to change the color of the LEDs on the hub."""
    POWER: int = 0
    CONNECT: int = 1
    @staticmethod
    def color(light_id: int, color_id: int) -> None:
        """Change the color of a light on the hub.
        
        Args:
            light_id: The light constant (POWER/CONNECT).
            color_id: A color constant from the color module.
        """
        ...

class light_matrix:
    """Module to control the 5x5 Light Matrix on the SPIKE Prime hub."""
    IMAGE_HEART: int = 1
    IMAGE_HEART_SMALL: int = 2
    IMAGE_HAPPY: int = 3
    IMAGE_SMILE: int = 4
    # ... (total 67 images)
    @staticmethod
    def clear() -> None:
        """Switches off all pixels on the Light Matrix."""
        ...
    @staticmethod
    def get_orientation() -> int:
        """Retrieve the current orientation of the Light Matrix."""
        ...
    @staticmethod
    def get_pixel(x: int, y: int) -> int:
        """Retrieve the intensity of a specific pixel (0-4, 0-4).
        
        Args:
            x: X coordinate (0-4).
            y: Y coordinate (0-4).
        """
        ...
    @staticmethod
    def set_orientation(top: int) -> int:
        """Change the orientation of the Light Matrix.
        
        Args:
            top: The side of the hub to be the top (UP, LEFT, RIGHT, DOWN).
        """
        ...
    @staticmethod
    def set_pixel(x: int, y: int, intensity: int) -> None:
        """Sets the brightness of one pixel (0-100).
        
        Args:
            x: X coordinate (0-4).
            y: Y coordinate (0-4).
            intensity: Brightness (0-100).
        """
        ...
    @staticmethod
    def show(pixels: Iterable[int]) -> None:
        """Change all 25 pixels at once using a list of intensity values.
        
        Args:
            pixels: Iterable of 25 intensity values.
        """
        ...
    @staticmethod
    def show_image(image: int) -> None:
        """Display one of the built-in images.
        
        Args:
            image: Image ID (1-67).
        """
        ...
    @staticmethod
    def write(text: str, intensity: int = 100, time_per_character: int = 500) -> Awaitable[None]:
        """Displays scrolling text on the Light Matrix.
        
        Args:
            text: Text to display.
            intensity: Brightness (0-100).
            time_per_character: Time in milliseconds per character.
        """
        ...

class motion_sensor:
    """Module to get data from the 6-axis IMU inside the hub."""
    TAPPED: int = 0
    DOUBLE_TAPPED: int = 1
    SHAKEN: int = 2
    FALLING: int = 3
    UNKNOWN: int = -1
    TOP: int = 0
    FRONT: int = 1
    RIGHT: int = 2
    BOTTOM: int = 3
    BACK: int = 4
    LEFT: int = 5

    @staticmethod
    def acceleration(raw_unfiltered: bool = False) -> Tuple[int, int, int]:
        """Returns (x, y, z) acceleration in milli-G (1/1000 G).
        
        Args:
            raw_unfiltered: Whether to return raw data.
        """
        ...
    @staticmethod
    def angular_velocity(raw_unfiltered: bool = False) -> Tuple[int, int, int]:
        """Returns (x, y, z) angular velocity in decidegrees/sec.
        
        Args:
            raw_unfiltered: Whether to return raw data.
        """
        ...
    @staticmethod
    def gesture() -> int:
        """Returns the recognized gesture (TAPPED, SHAKEN, etc.)."""
        ...
    @staticmethod
    def get_yaw_face() -> int:
        """Retrieve the face of the hub that yaw is relative to."""
        ...
    @staticmethod
    def quaternion() -> Tuple[float, float, float, float]:
        """Returns the hub orientation quaternion (w, x, y, z)."""
        ...
    @staticmethod
    def reset_tap_count() -> None:
        """Reset the tap count."""
        ...
    @staticmethod
    def reset_yaw(angle: int) -> None:
        """Change the yaw angle offset.
        
        Args:
            angle: The new yaw value.
        """
        ...
    @staticmethod
    def set_yaw_face(up: int) -> bool:
        """Change what hub face is used as the yaw face."""
        ...
    @staticmethod
    def stable() -> bool:
        """Check if the hub is resting flat."""
        ...
    @staticmethod
    def tap_count() -> int:
        """Returns the number of taps since start or reset."""
        ...
    @staticmethod
    def tilt_angles() -> Tuple[int, int, int]:
        """Returns (yaw, pitch, roll) in decidegrees."""
        ...
    @staticmethod
    def up_face() -> int:
        """Returns the hub face that is currently facing up."""
        ...

class port:
    """Constants for port access (A, B, C, D, E, F)."""
    A: int = 0
    B: int = 1
    C: int = 2
    D: int = 3
    E: int = 4
    F: int = 5

class sound:
    """Module to play synthesized beeps and manage volume on the hub."""
    ANY: int = -2
    DEFAULT: int = -1
    WAVEFORM_SINE: int = 1
    WAVEFORM_SQUARE: int = 2
    WAVEFORM_SAWTOOTH: int = 3
    WAVEFORM_TRIANGLE: int = 1
    @staticmethod
    def beep(freq: int = 440, duration: int = 500, volume: int = 100, *, attack: int = 0, decay: int = 0, sustain: int = 100, release: int = 0, transition: int = 10, waveform: int = 1, channel: int = -1) -> Awaitable[None]:
        """Plays a synthesized beep from the hub speaker.
        
        Args:
            freq: Frequency in Hz.
            duration: Duration in ms.
            volume: Volume (0-100).
            waveform: Synthetic waveform (from sound module).
        """
        ...
    @staticmethod
    def stop() -> None:
        """Stop all sound from the hub."""
        ...
    @staticmethod
    def volume(volume: int) -> None:
        """Set the speaker volume (0-100).
        
        Args:
            volume: Target volume level.
        """
        ...
