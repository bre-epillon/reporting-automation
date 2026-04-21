import sys
from datetime import datetime


# Define ANSI escape codes for colors.
# This class makes it easy to reference the colors by name.
class Color:
    """
    A class containing ANSI escape codes for text coloring in the terminal.

    These codes are used to change the color of printed text.
    The RESET code is crucial to ensure subsequent prints are not colored.
    """

    INFO = "\033[94m"  # Blue
    SUCCESS = "\033[92m"  # Green
    WARNING = "\033[93m"  # Yellow
    ERROR = "\033[91m"  # Red
    DEBUG = "\033[96m"  # Cyan
    RESET = "\033[0m"  # Resets color to default


def _log(message: str, color: str):
    """
    The core function to print a colored message to the terminal.

    This function handles the actual printing, applying the color code
    before the message and the reset code after it.

    Args:
        message (str): The log message to display.
        color (str): The ANSI color code from the Color class.
    """
    # Print the colored message to standard output.
    # The `f-string` combines the color code, message, and reset code.
    timestamp = "[{0:%Y-%m-%d %H:%M:%S}]".format(datetime.now())
    print(f"{color}{timestamp}: {message}{Color.RESET}", file=sys.stdout)


def info(message: str):
    """Logs an informational message in blue."""
    _log(f"INFO: {message}", Color.INFO)


def warning(message: str):
    """Logs a warning message in yellow."""
    _log(f"WARNING: {message}", Color.WARNING)


def error(message: str):
    """Logs an error message in red."""
    _log(f"ERROR: {message}", Color.ERROR)


def debug(message: str):
    """Logs a debug message in cyan."""
    _log(f"DEBUG: {message}", Color.DEBUG)


def success(message: str):
    """Logs a success message in green."""
    _log(f"SUCCESS: {message}", Color.SUCCESS)


# Example usage:
if __name__ == "__main__":
    # You can call these functions directly from your code.
    info("Application has started successfully.")
    warning("This is an important warning to consider.")
    error("An unhandled exception occurred.")
    debug("This is a detailed debug message for developers.")
