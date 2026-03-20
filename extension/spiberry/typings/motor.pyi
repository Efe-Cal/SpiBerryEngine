from typing import Any, Awaitable, Callable, Iterable, List, Optional, Tuple, Union

"""The motor module contains functions to control individual motors."""
READY: int = 0
RUNNING: int = 1
STALLED: int = 2
CANCELLED: int = 3
ERROR: int = 4
DISCONNECTED: int = 5
COAST: int = 0
BRAKE: int = 1
HOLD: int = 2
CONTINUE: int = 3
SMART_COAST: int = 4
SMART_BRAKE: int = 5
CLOCKWISE: int = 0
COUNTERCLOCKWISE: int = 1
SHORTEST_PATH: int = 2
LONGEST_PATH: int = 3

@staticmethod
def absolute_position(port: int) -> int:
    """Get the absolute position of a Motor.
    
    Args:
        port: Port ID.
    """
    ...
@staticmethod
def get_duty_cycle(port: int) -> int:
    """Get the current PWM duty cycle of a Motor.
    
    Args:
        port: Port ID.
    """
    ...
@staticmethod
def relative_position(port: int) -> int:
    """Get the relative position of a Motor.
    
    Args:
        port: Port ID.
    """
    ...
@staticmethod
def reset_relative_position(port: int, position: int) -> None:
    """Reset the relative position offset of a Motor.
    
    Args:
        port: Port ID.
        position: New relative position (degrees).
    """
    ...
@staticmethod
def run(port: int, velocity: int, *, acceleration: int = 1000) -> None:
    """Start a Motor at a constant speed until a new command is given.
    
    Args:
        port: Port ID.
        velocity: Speed (deg/sec).
        acceleration: Acceleration (deg/sec²).
    """
    ...
@staticmethod
def run_for_degrees(port: int, degrees: int, velocity: int, *, stop: int = 1, acceleration: int = 1000, deceleration: int = 1000) -> Awaitable[int]:
    """Turn a motor for a specific number of degrees.
    
    Args:
        port: Port ID.
        degrees: Relative degrees.
        velocity: Speed (deg/sec).
        stop: Behavior (COAST, BRAKE, HOLD, ...).
    """
    ...
@staticmethod
def run_for_time(port: int, duration: int, velocity: int, *, stop: int = 1, acceleration: int = 1000, deceleration: int = 1000) -> Awaitable[int]:
    """Run a motor for a limited amount of time (milliseconds).
    
    Args:
        port: Port ID.
        duration: Milliseconds.
        velocity: Speed (deg/sec).
    """
    ...
@staticmethod
def run_to_absolute_position(port: int, position: int, velocity: int, *, direction: int = 2, stop: int = 1, acceleration: int = 1000, deceleration: int = 1000) -> Awaitable[int]:
    """Turn a motor to an absolute position.
    
    Args:
        port: Port ID.
        position: Absolute position (0-359).
        velocity: Speed (deg/sec).
        direction: CLOCKWISE, COUNTERCLOCKWISE, SHORTEST_PATH, LONGEST_PATH.
    """
    ...
@staticmethod
def run_to_relative_position(port: int, position: int, velocity: int, *, stop: int = 1, acceleration: int = 1000, deceleration: int = 1000) -> Awaitable[int]:
    """Turn a motor for a relative position (degrees)."""
    ...
@staticmethod
def set_duty_cycle(port: int, pwm: int) -> None:
    """Start a Motor with a specific PWM (-10000 to 10000)."""
    ...
@staticmethod
def stop(port: int, *, stop: int = 1) -> None:
    """Stops a motor.
    
    Args:
        port: Port ID.
        stop: Behavior (COAST, BRAKE, HOLD, ...).
    """
    ...
@staticmethod
def velocity(port: int) -> int:
    """Get the current velocity (deg/sec) of a Motor."""
    ...