"""
Worker.
"""


def fib(number: int) -> int:
    """Fibonacci example function

    Args:
      n (int): integer

    Returns:
      int: n-th Fibonacci number
    """
    assert number > 0

    if number in (1, 2):
        return 1
    return fib(number - 1) + fib(number - 2)
