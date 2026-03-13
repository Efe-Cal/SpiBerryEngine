from typing import Any, Awaitable, Callable, Iterable, List, Optional, Tuple, Union

class hub:
    @staticmethod
    def device_uuid() -> str: ...
    @staticmethod
    def hardware_id() -> str: ...
    @staticmethod
    def power_off() -> int: ...
    @staticmethod
    def temperature() -> int: ...

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
