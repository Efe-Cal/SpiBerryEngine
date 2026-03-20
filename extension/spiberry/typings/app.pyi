from typing import Any, Awaitable, Callable, Iterable, List, Optional, Tuple, Union


class bargraph:
    """The bargraph module is used make bar graphs in the SPIKE App"""
    @staticmethod
    def change(color: int, value: float) -> None:
        """Change the value of a bar in the bargraph.
        
        Args:
            color: A color from the color module.
            value: The value to change by.
        """
        ...
    @staticmethod
    def clear_all() -> None:
        """Clear all bars in the bargraph."""
        ...
    @staticmethod
    def get_value(color: int) -> Awaitable[float]:
        """Retrieve the value of a bar in the bargraph.
        
        Args:
            color: A color from the color module.
        """
        ...
    @staticmethod
    def hide() -> None:
        """Hide the bargraph in the SPIKE App."""
        ...
    @staticmethod
    def set_value(color: int, value: float) -> None:
        """Set the value of a bar in the bargraph.
        
        Args:
            color: A color from the color module.
            value: The value to set.
        """
        ...
    @staticmethod
    def show(fullscreen: bool) -> None:
        """Show the bargraph in the SPIKE App.
        
        Args:
            fullscreen: Whether to show in full screen.
        """
        ...

class display:
    """The display module is used show images in the SPIKE App"""
    IMAGE_ROBOT_1: int = 1
    IMAGE_ROBOT_2: int = 2
    IMAGE_ROBOT_3: int = 3
    IMAGE_ROBOT_4: int = 4
    IMAGE_ROBOT_5: int = 5
    IMAGE_HUB_1: int = 6
    IMAGE_HUB_2: int = 7
    IMAGE_HUB_3: int = 8
    IMAGE_HUB_4: int = 9
    IMAGE_AMUSEMENT_PARK: int = 10
    IMAGE_BEACH: int = 11
    IMAGE_HAUNTED_HOUSE: int = 12
    IMAGE_CARNIVAL: int = 13
    IMAGE_BOOKSHELF: int = 14
    IMAGE_PLAYGROUND: int = 15
    IMAGE_MOON: int = 16
    IMAGE_CAVE: int = 17
    IMAGE_OCEAN: int = 18
    IMAGE_POLAR_BEAR: int = 19
    IMAGE_PARK: int = 20
    IMAGE_RANDOM: int = 21

    @staticmethod
    def hide() -> None:
        """Hide the display in the SPIKE App."""
        ...
    @staticmethod
    def image(image: int) -> None:
        """Show an image on the display in the SPIKE App.
        
        Args:
            image: The ID of the image to show (1-21).
        """
        ...
    @staticmethod
    def show(fullscreen: bool) -> None:
        """Show the display in the SPIKE App.
        
        Args:
            fullscreen: Whether to show in full screen.
        """
        ...
    @staticmethod
    def text(text: str) -> None:
        """Show text on the display in the SPIKE App.
        
        Args:
            text: The text to display.
        """
        ...

class linegraph:
    """The linegraph module is used make line graphs in the SPIKE App"""
    @staticmethod
    def clear(color: int) -> None:
        """Clear a specific line in the linegraph.
        
        Args:
            color: A color from the color module.
        """
        ...
    @staticmethod
    def clear_all() -> None:
        """Clear all lines in the linegraph."""
        ...
    @staticmethod
    def get_average(color: int) -> Awaitable[float]:
        """Retrieve the average value of a line in the linegraph.
        
        Args:
            color: A color from the color module.
        """
        ...
    @staticmethod
    def get_last(color: int) -> Awaitable[float]:
        """Retrieve the last value of a line in the linegraph.
        
        Args:
            color: A color from the color module.
        """
        ...
    @staticmethod
    def get_max(color: int) -> Awaitable[float]:
        """Retrieve the maximum value of a line in the linegraph.
        
        Args:
            color: A color from the color module.
        """
        ...
    @staticmethod
    def get_min(color: int) -> Awaitable[float]:
        """Retrieve the minimum value of a line in the linegraph.
        
        Args:
            color: A color from the color module.
        """
        ...
    @staticmethod
    def hide() -> None:
        """Hide the linegraph in the SPIKE App."""
        ...
    @staticmethod
    def plot(color: int, x: float, y: float) -> None:
        """Plot a point on a line in the linegraph.
        
        Args:
            color: A color from the color module.
            x: The X value.
            y: The Y value.
        """
        ...
    @staticmethod
    def show(fullscreen: bool) -> None:
        """Show the linegraph in the SPIKE App.
        
        Args:
            fullscreen: Whether to show in full screen.
        """
        ...

class music:
    """The music module is used make music in the SPIKE App"""
    DRUM_BASS: int = 2
    DRUM_BONGO: int = 13
    # ... (other DRUM constants)
    INSTRUMENT_PIANO: int = 1
    # ... (other INSTRUMENT constants)
    @staticmethod
    def play_drum(drum: int) -> None:
        """Play a drum sound in the SPIKE App.
        
        Args:
            drum: The drum ID.
        """
        ...
    @staticmethod
    def play_instrument(instrument: int, note: int, duration: int) -> None:
        """Play an instrument note in the SPIKE App.
        
        Args:
            instrument: The instrument ID.
            note: The MIDI note (0-130).
            duration: Duration in milliseconds.
        """
        ...

class sound:
    """The sound module is used play sounds in the SPIKE App"""
    @staticmethod
    def play(sound_name: str, volume: int = 100, pitch: int = 0, pan: int = 0) -> Awaitable[None]:
        """Play a sound in the SPIKE App.
        
        Args:
            sound_name: The sound name.
            volume: Volume (0-100).
            pitch: Pitch adjustment.
            pan: Pan effect (-100 to 100).
        """
        ...
    @staticmethod
    def set_attributes(volume: int, pitch: int, pan: int) -> None:
        """Set default sound attributes for the SPIKE App.
        
        Args:
            volume: Volume (0-100).
            pitch: Pitch adjustment.
            pan: Pan effect (-100 to 100).
        """
        ...
    @staticmethod
    def stop() -> None:
        """Stop all sounds currently playing in the SPIKE App."""
        ...


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
    LEFT: int = 1
    RIGHT: int = 2
    @staticmethod
    def pressed(button: int) -> int: ...

class light:
    POWER: int = 0
    CONNECT: int = 1
    @staticmethod
    def color(light_id: int, color_id: int) -> None: ...

class light_matrix:
    IMAGE_HEART: int = 1
    IMAGE_HEART_SMALL: int = 2
    IMAGE_HAPPY: int = 3
    IMAGE_SMILE: int = 4
    # ... (total 67 images)
    @staticmethod
    def clear() -> None: ...
    @staticmethod
    def get_orientation() -> int: ...
    @staticmethod
    def get_pixel(x: int, y: int) -> int: ...
    @staticmethod
    def set_orientation(top: int) -> int: ...
    @staticmethod
    def set_pixel(x: int, y: int, intensity: int) -> None: ...
    @staticmethod
    def show(pixels: Iterable[int]) -> None: ...
    @staticmethod
    def show_image(image: int) -> None: ...
    @staticmethod
    def write(text: str, intensity: int = 100, time_per_character: int = 500) -> Awaitable[None]: ...

class motion_sensor:
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
    def acceleration(raw_unfiltered: bool = False) -> Tuple[int, int, int]: ...
    @staticmethod
    def angular_velocity(raw_unfiltered: bool = False) -> Tuple[int, int, int]: ...
    @staticmethod
    def gesture() -> int: ...
    @staticmethod
    def get_yaw_face() -> int: ...
    @staticmethod
    def quaternion() -> Tuple[float, float, float, float]: ...
    @staticmethod
    def reset_tap_count() -> None: ...
    @staticmethod
    def reset_yaw(angle: int) -> None: ...
    @staticmethod
    def set_yaw_face(up: int) -> bool: ...
    @staticmethod
    def stable() -> bool: ...
    @staticmethod
    def tap_count() -> int: ...
    @staticmethod
    def tilt_angles() -> Tuple[int, int, int]: ...
    @staticmethod
    def up_face() -> int: ...

class port:
    A: int = 0
    B: int = 1
    C: int = 2
    D: int = 3
    E: int = 4
    F: int = 5

class sound:
    ANY: int = -2
    DEFAULT: int = -1
    WAVEFORM_SINE: int = 1
    WAVEFORM_SQUARE: int = 2
    WAVEFORM_SAWTOOTH: int = 3
    WAVEFORM_TRIANGLE: int = 1
    @staticmethod
    def beep(freq: int = 440, duration: int = 500, volume: int = 100, *, attack: int = 0, decay: int = 0, sustain: int = 100, release: int = 0, transition: int = 10, waveform: int = 1, channel: int = -1) -> Awaitable[None]: ...
    @staticmethod
    def stop() -> None: ...
    @staticmethod
    def volume(volume: int) -> None: ...
