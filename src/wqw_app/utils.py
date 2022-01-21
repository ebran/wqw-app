"""Utility functions."""
track_progress_key_prefix = "arq:track:"  # pylint: disable=invalid-name


def removeprefix(str_with_prefix: str, prefix: str) -> str:
    """Remove prefix from a string."""
    return (
        str_with_prefix[len(prefix) :]
        if str_with_prefix.startswith(prefix)
        else str_with_prefix
    )
