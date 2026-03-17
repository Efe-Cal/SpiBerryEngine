from typing import Any, Awaitable, Callable, Iterable, List, Optional, Tuple, Union

class device:
    """The device module enables you to get information about devices plugged into the hub."""
    @staticmethod
    def data(port: int) -> Tuple[int, ...]:
        """Retrieve the raw LPF-2 data from a device.
        
        Args:
            port: A port ID (e.g. from hub.port).
        """
        ...
    @staticmethod
    def id(port: int) -> int:
        """Retrieve the device ID for a device.
        
        Args:
            port: A port ID (e.g. from hub.port).
        """
        ...
    @staticmethod
    def get_duty_cycle(port: int) -> int:
        """Retrieve the duty cycle for a device. Value in range 0 to 10000.
        
        Args:
            port: A port ID (e.g. from hub.port).
        """
        ...
    @staticmethod
    def ready(port: int) -> bool:
        """Check if a device is ready to accept requests.
        
        Args:
            port: A port ID (e.g. from hub.port).
        """
        ...
    @staticmethod
    def set_duty_cycle(port: int, duty_cycle: int) -> None:
        """Set the duty cycle on a device (0-10000).
        
        Args:
            port: A port ID (e.g. from hub.port).
            duty_cycle: The PWM value (0-10000).
        """
        ...
