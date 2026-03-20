from typing import Any, Awaitable, Callable, Iterable, List, Optional, Tuple, Union

"""The runloop module contains functions for async execution control and scheduling."""
@staticmethod
def run(*functions: Awaitable[Any]) -> None:
    """Start one or more parallel async functions.
    
    Args:
        *functions: Awaitable functions to run concurrently.
    """
    ...
@staticmethod
def sleep_ms(duration: int) -> Awaitable[None]:
    """Awaits for a duration in milliseconds without blocking other parallel functions.
    
    Args:
        duration: Time in milliseconds.
    """
    ...
@staticmethod
def until(function: Callable[[], bool], timeout: int = 0) -> Awaitable[None]:
    """Await until a condition function returns True or timeout is reached.
    
    Args:
        function: A predicate function returning bool.
        timeout: Timeout in milliseconds (0 = no timeout).
    """
    ...
