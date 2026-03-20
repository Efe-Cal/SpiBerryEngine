from typing import Any, Awaitable, Callable, Iterable, List, Optional, Tuple, Union


"""The color_matrix module is used to control the Color Matrix on SPIKE Prime motors or other peripherals."""
@staticmethod
def clear(port: int) -> None:
    """Turn off all pixels on a Color Matrix.
    
    Args:
        port: A port ID (e.g. from hub.port).
    """
    ...
@staticmethod
def get_pixel(port: int, x: int, y: int) -> Tuple[int, int]:
    """Retrieve a specific pixel's color and intensity.
    
    Args:
        port: A port ID (e.g. from hub.port).
        x: The X coordinate (0-2).
        y: The Y coordinate (0-2).
        
    Returns:
        A tuple containing (color, intensity).
    """
    ...
@staticmethod
def set_pixel(port: int, x: int, y: int, pixel: Tuple[int, int]) -> None:
    """Change a single pixel on a Color Matrix.
    
    Args:
        port: A port ID (e.g. from hub.port).
        x: The X coordinate (0-2).
        y: The Y coordinate (0-2).
        pixel: A tuple containing (color, intensity).
    """
    ...
@staticmethod
def show(port: int, pixels: List[Tuple[int, int]]) -> None:
    """Change all 9 pixels at once on a Color Matrix.
    
    Args:
        port: A port ID (e.g. from hub.port).
        pixels: A list of 9 tuples, each containing (color, intensity).
    """
    ...
