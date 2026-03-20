from typing import Any, Awaitable, Callable, Iterable, List, Optional, Tuple, Union


"""The color_sensor module enables you to write code that reacts to specific colors or light intensity."""
@staticmethod
def color(port: int) -> int:
    """Returns the color value of the detected color.
    
    Args:
        port: A port ID (e.g. from hub.port).
    """
    ...
@staticmethod
def reflection(port: int) -> int:
    """Retrieves the intensity of the reflected light (0-100%).
    
    Args:
        port: A port ID (e.g. from hub.port).
    """
    ...
@staticmethod
def rgbi(port: int) -> Tuple[int, int, int, int]:
    """Retrieves the overall color intensity and intensity of red, green, and blue.
    
    Args:
        port: A port ID (e.g. from hub.port).
        
    Returns:
        A tuple containing (red, green, blue, overall intensity).
    """
    ...
