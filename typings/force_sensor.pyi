from typing import Any, Awaitable, Callable, Iterable, List, Optional, Tuple, Union

class force_sensor:
    """The force_sensor module contains functions to use the Force Sensor."""
    @staticmethod
    def force(port: int) -> int:
        """Retrieves measured force as decinewton (0-100).
        
        Args:
            port: A port ID (e.g. from hub.port).
        """
        ...
    @staticmethod
    def pressed(port: int) -> bool:
        """Tests whether the button on the sensor is pressed.
        
        Args:
            port: A port ID (e.g. from hub.port).
        """
        ...
    @staticmethod
    def raw(port: int) -> int:
        """Returns the raw, uncalibrated force value.
        
        Args:
            port: A port ID (e.g. from hub.port).
        """
        ...
