from typing import Any, Awaitable, Callable, Iterable, List, Optional, Tuple, Union


"""The motor_pair module is used to run motors in a synchronized fashion (e.g. for drivebases)."""
PAIR_1: int = 0
PAIR_2: int = 1
PAIR_3: int = 2
@staticmethod
def move(pair: int, steering: int, *, velocity: int = 360, acceleration: int = 1000) -> None:
    """Move a Motor Pair at a constant speed until a new command is given.
    
    Args:
        pair: A pair slot constant (PAIR_1, PAIR_2, PAIR_3).
        steering: Steering value (-100 to 100). 0 is straight.
        velocity: Velocity (deg/sec).
        acceleration: Acceleration (deg/sec²).
    """
    ...
@staticmethod
def move_for_degrees(pair: int, degrees: int, steering: int, *, velocity: int = 360, stop: int = 1, acceleration: int = 1000, deceleration: int = 1000) -> Awaitable[int]:
    """Move a Motor Pair at a constant speed for a specific number of degrees.
    
    Args:
        pair: A pair slot constant (PAIR_1, PAIR_2, PAIR_3).
        degrees: Relative degrees.
        steering: Steering value (-100 to 100).
        velocity: Velocity (deg/sec).
    """
    ...
@staticmethod
def move_for_time(pair: int, duration: int, steering: int, *, velocity: int = 360, stop: int = 1, acceleration: int = 1000, deceleration: int = 1000) -> Awaitable[int]:
    """Move a Motor Pair for a specific duration (milliseconds).
    
    Args:
        pair: A pair slot constant (PAIR_1, PAIR_2, PAIR_3).
        duration: Milliseconds.
        steering: Steering value (-100 to 100).
    """
    ...
@staticmethod
def move_tank(pair: int, left_velocity: int, right_velocity: int, *, acceleration: int = 1000) -> None:
    """Perform a tank move on a Motor Pair until a new command is given.
    
    Args:
        pair: Pair slot.
        left_velocity: Speed of left motor.
        right_velocity: Speed of right motor.
    """
    ...
@staticmethod
def move_tank_for_degrees(pair: int, degrees: int, left_velocity: int, right_velocity: int, *, stop: int = 1, acceleration: int = 1000, deceleration: int = 1000) -> Awaitable[int]:
    """Perform a tank move on a Motor Pair for a specific number of degrees."""
    ...
@staticmethod
def move_tank_for_time(pair: int, left_velocity: int, right_velocity: int, duration: int, *, stop: int = 1, acceleration: int = 1000, deceleration: int = 1000) -> Awaitable[int]:
    """Perform a tank move on a Motor Pair for a specific amount of time (milliseconds)."""
    ...
@staticmethod
def pair(pair_slot: int, left_motor_port: int, right_motor_port: int) -> None:
    """Pair two motors together to use in further motor_pair module functions.
    
    Args:
        pair_slot: A constant (PAIR_1, PAIR_2, PAIR_3).
        left_motor_port: Port ID (e.g. hub.port.A).
        right_motor_port: Port ID (e.g. hub.port.B).
    """
    ...
@staticmethod
def stop(pair: int, *, stop: int = 1) -> None:
    """Stops a Motor Pair.
    
    Args:
        pair: Pair slot.
        stop: Behavior (from motor module: COAST, BRAKE, HOLD, etc.).
    """
    ...
@staticmethod
def unpair(pair: int) -> None:
    """Unpair a Motor Pair.
    
    Args:
        pair: Pair slot.
    """
    ...
