import unittest
import requests

from proxy_client import ProxyManager


class ProxyTest(unittest.TestCase):
    def test_opera(self):
        opera_server = ProxyManager.opera()
        opera_server.run()
        try:
            response = requests.get("https://api.ipify.org/", proxies=opera_server.proxies, timeout=10)
            print("Opera Proxy IP:", response.text)
        except Exception as e:
            print("Error using Opera proxy:", e)

        opera_server.stop()

    def test_hola(self):
        hola_server = ProxyManager.hola()
        hola_server.run()
        try:
            response = requests.get("https://api.ipify.org/", proxies=hola_server.proxies, timeout=10)
            print("Hola Proxy IP:", response.text)
        except Exception as e:
            print("Error using Hola proxy:", e)

        hola_server.stop()


if __name__ == "__main__":
    unittest.main()
