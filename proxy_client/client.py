import subprocess
import threading
import os
import time
import sys
from typing import Optional

from .utils import get_random_free_port

INIT_TIMEOUT = 30


class ProxyServer:
    """Manages a proxy server process, handling its lifecycle and configuration."""

    def __init__(self, proxy_name: str, port: str, country: Optional[str] = None, residential: Optional[bool] = False, init_timeout: Optional[int] = None):
        """Initialize the ProxyServer class.

        Args:
            proxy_name (str): The name of the proxy server program.
            port (str): The port the server will bind to.  If None, a random free port is used.
            country (Optional[str]):  The country code for the proxy (e.g., "us", "gb").  If provided, configures the proxy for a specific country.
            residential (Optional[bool]): Whether to use residential proxy type. Defaults to False.
            init_timeout (Optional[int]):  Timeout in seconds to wait for the proxy server to initialize. Defaults to INIT_TIMEOUT.
        """
        self.host = "localhost"
        self.port = port or get_random_free_port()
        self.proxy_name = proxy_name
        self.residential = residential
        self.country = country
        self.ininit_timeout = init_timeout or INIT_TIMEOUT
        self.process = None
        self.thread = None
        self.running = False
        self.initialized = False
        self.proxies = {
            "http": f"http://{self.host}:{self.port}",
            "https": f"http://{self.host}:{self.port}",
        }

    def __enter__(self):
        self.run()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    def _construct_command(self) -> list[str]:
        """Construct the command to run the proxy.

        Returns:
            list[str]: The command to execute, as a list of strings.
        """
        cmd = [self.proxy_name, "-bind-address", f"{self.host}:{self.port}"]
        if self.residential:
            cmd.extend(["-proxy-type", "lum"])
        if self.country:
            cmd.extend(["-country", self.country])
        return cmd

    def _wait_for_initialization(self):
        """Waits for the server to be initialized and ready to accept connections.

        Raises:
            Exception: If the proxy server fails to initialize within the specified timeout.
        """
        start_time = time.time()
        while not self.initialized and time.time() - start_time < self.ininit_timeout:
            time.sleep(0.5)  # Check every half second

        if not self.initialized:
            self.stop()
            raise Exception(f"{self.proxy_name} proxy failed to initialize within {self.ininit_timeout} seconds.")

    def run(self):
        """Start the proxy server and monitor its output.  This method blocks until the server is initialized."""

        def target():
            try:
                command = self._construct_command()
                # Start the subprocess, capturing both stdout and stderr
                self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=os.environ, bufsize=1)  # Added bufsize=1
                self.running = True

                # Monitor the output
                for line in iter(self.process.stdout.readline, ""):
                    sys.stdout.write(line)  # Use sys.stdout.write
                    sys.stdout.flush()  # and sys.stdout.flush
                    if "Init complete" in line:
                        print(f"{self.proxy_name} proxy server initialized successfully.")  # keep the print for user experience
                        self.initialized = True
                        break

                # Continue reading output after initialization
                for line in iter(self.process.stdout.readline, ""):
                    sys.stdout.write(line)  # Use sys.stdout.write
                    sys.stdout.flush()  # and sys.stdout.flush

            except Exception as e:
                print(f"Error running {self.proxy_name}: {e}")
            finally:
                self.running = False
                if self.process:
                    self.process.stdout.close()
                    if self.process.stderr:  # Check if stderr exists
                        self.process.stderr.close()
                    self.process.wait()

        # Run the monitoring in a thread
        self.thread = threading.Thread(target=target)
        self.thread.start()
        self._wait_for_initialization()  # wait for server init before returning

    def stop(self):
        """Stop the proxy server.  Attempts graceful termination first, then forces a kill if necessary."""
        if self.process and self.running:
            print(f"Stopping {self.proxy_name} proxy server...")
            try:
                # Attempt graceful termination first
                self.process.terminate()
                self.process.wait(timeout=5)  # give it 5 seconds to terminate gracefully

            except subprocess.TimeoutExpired:
                # If it doesn't terminate, send a SIGKILL as a last resort
                print(f"Warning: {self.proxy_name} proxy server did not terminate gracefully. Forcing kill.")
                self.process.kill()
                self.process.wait()

            except Exception as e:
                print(f"Error stopping {self.proxy_name} proxy server: {e}")
            finally:
                self.running = False
                print(f"{self.proxy_name} proxy server stopped.")
        if self.thread:
            self.thread.join()


class ProxyManager:
    """Factory class for creating different types of proxy servers."""

    @classmethod
    def opera(
        cls,
        port: Optional[str] = None,
        country: Optional[str] = None,
        init_timeout: Optional[int] = INIT_TIMEOUT,
    ) -> ProxyServer:
        """Create an Opera proxy server.

        Args:
            port (Optional[str]): The port the server will bind to. If None, a random port is used.
            country (Optional[str]): The country to configure the proxy for.
            init_timeout (Optional[int]): Initialization timeout in seconds.

        Returns:
            ProxyServer: Configured ProxyServer instance.
        """
        return cls._create_proxy(proxy_name="opera-proxy", port=port, country=country, init_timeout=init_timeout)

    @classmethod
    def hola(
        cls,
        port: Optional[str] = None,
        country: Optional[str] = None,
        residential: Optional[bool] = True,
        init_timeout: Optional[int] = INIT_TIMEOUT,
    ) -> ProxyServer:
        """Create a Hola proxy server with residential IP support.

        Args:
            port (Optional[str]): The port the server will bind to. If None, a random port is used.
            country (Optional[str]): The country to configure the proxy for.
            residential (Optional[bool]): Whether to use residential proxy type. Defaults to True.
            init_timeout (Optional[int]): Initialization timeout in seconds.

        Returns:
            ProxyServer: Configured ProxyServer instance.
        """
        return cls._create_proxy(proxy_name="hola-proxy", port=port, country=country, residential=residential, init_timeout=init_timeout)

    @classmethod
    def _create_proxy(
        cls,
        proxy_name: str,
        port: Optional[str] = None,
        country: Optional[str] = None,
        residential: bool = False,
        init_timeout: Optional[int] = INIT_TIMEOUT,
    ) -> ProxyServer:
        """Factory method to create a ProxyServer instance.

        Args:
            proxy_name (str): The name of the proxy server program.
            port (Optional[str]): The port the server will bind to. If None, a random port is used.
            country (Optional[str]): The country to configure the proxy for.
            residential (bool): Whether to use residential proxy type. Defaults to False.
            init_timeout (Optional[int]): Initialization timeout in seconds.

        Returns:
            ProxyServer: Configured ProxyServer instance.
        """
        return ProxyServer(proxy_name, port, country, residential, init_timeout)
