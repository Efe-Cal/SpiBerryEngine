from typing import Any, Awaitable, Callable, Iterable, List, Optional, Tuple, Union

class motor:
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
    def absolute_position(port: int) -> int: ...
    @staticmethod
    def get_duty_cycle(port: int) -> int: ...
    @staticmethod
    def relative_position(port: int) -> int: ...
    @staticmethod
    def reset_relative_position(port: int, position: int) -> None: ...
    @staticmethod
    def run(port: int, velocity: int, *, acceleration: int = 1000) -> None: ...
    @staticmethod
    def run_for_degrees(port: int, degrees: int, velocity: int, *, stop: int = 1, acceleration: int = 1000, deceleration: int = 1000) -> Awaitable[int]: ...
    @staticmethod
    def run_for_time(port: int, duration: int, velocity: int, *, stop: int = 1, acceleration: int = 1000, deceleration: int = 1000) -> Awaitable[int]: ...
    @staticmethod
    def run_to_absolute_position(port: int, position: int, velocity: int, *, direction: int = 2, stop: int = 1, acceleration: int = 1000, deceleration: int = 1000) -> Awaitable[int]: ...
    @staticmethod
    def run_to_relative_position(port: int, position: int, velocity: int, *, stop: int = 1, acceleration: int = 1000, deceleration: int = 1000) -> Awaitable[int]: ...
    @staticmethod
    def set_duty_cycle(port: int, pwm: int) -> None: ...
    @staticmethod
    def stop(port: int, *, stop: int = 1) -> None: ...
    @staticmethod
    def velocity(port: int) -> int: ...