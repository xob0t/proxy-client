import socket
from contextlib import closing
import random


def get_random_free_port(start_port=1024, end_port=65535, max_attempts=100, bind_address=""):
    """
    Finds a random, unused port on the local machine.

    Args:
        start_port (int): The minimum port number to consider (inclusive).  Defaults to 1024.
        end_port (int): The maximum port number to consider (inclusive). Defaults to 65535.
        max_attempts (int): The maximum number of attempts to find an unused port.
        bind_address (str): The address to bind to.  Defaults to "" (all interfaces).  Can be "127.0.0.1" for localhost only.

    Returns:
        int: A free port number.

    Raises:
        ValueError: If the port range is invalid or start_port > end_port.
        RuntimeError: If no free port is found after max_attempts.
    """

    if not (1 <= start_port <= 65535) or not (1 <= end_port <= 65535):
        raise ValueError("Port numbers must be between 1 and 65535")

    if start_port > end_port:
        raise ValueError("Start port must be less than or equal to end port")

    for _ in range(max_attempts):
        port = random.randint(start_port, end_port)
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            try:
                sock.bind((bind_address, port))  # Try to bind to the port
                return port  # If binding succeeds, the port is unused
            except (socket.error, OSError) as e:
                # Check for common "address already in use" error codes
                if isinstance(e, OSError) and (e.errno == 98 or e.errno == 48):  # 98: Linux/Unix, 48: Windows
                    continue  # Port is in use, try another
                else:
                    raise  # Re-raise unexpected exceptions

    raise RuntimeError(f"Could not find a free port after {max_attempts} attempts")


def test_port_availability(port, bind_address=""):
    """
    Test if a specific port is available.

    Args:
        port (int): Port number to test
        bind_address (str): The address to bind. Defaults to "" (all interfaces).

    Returns:
        bool: True if port is available, False otherwise
    """
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        try:
            sock.bind((bind_address, port))
            return True
        except (socket.error, OSError):
            return False
