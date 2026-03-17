from typing import Any, Awaitable, Callable, Iterable, List, Optional, Tuple, Union

class distance_sensor:
    """The distance_sensor module enables you to react to distances or control sensor LEDs."""
    @staticmethod
    def clear(port: int) -> None:
        """Turns off all the lights in the Distance Sensor.
        
        Args:
            port: A port ID (e.g. from hub.port).
        """
        ...
    @staticmethod
    def distance(port: int) -> int:
        """Retrieve the distance in millimeters captured by the sensor (-1 if invalid).
        
        Args:
            port: A port ID (e.g. from hub.port).
        """
        ...
    @staticmethod
    def get_pixel(port: int, x: int, y: int) -> int:
        """Retrieve the intensity of a specific LED on the sensor.
        
        Args:
            port: A port ID (e.g. from hub.port).
            x: The X coordinate (0-3).
            y: The Y coordinate (0-3).
        """
        ...
    @staticmethod
    def set_pixel(port: int, x: int, y: int, intensity: int) -> None:
        """Changes the intensity of a specific LED on the sensor.
        
        Args:
            port: A port ID (e.g. from hub.port).
            x: The X coordinate (0-3).
            y: The Y coordinate (0-3).
            intensity: How bright to light up the pixel (0-100).
        """
        ...
    @staticmethod
    def show(port: int, pixels: List[int]) -> None:
        """Change all the lights at the same time on the distance sensor.
        
        Args:
            port: A port ID (e.g. from hub.port).
            pixels: A list of 4 intensity values.
        """
        ...
