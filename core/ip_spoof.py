import random
import socket
import struct

def random_ip():
    """Generate random IPv4 address"""
    return socket.inet_ntoa(struct.pack(">I", random.randint(1, 0xffffffff)))

def random_ip_in_subnet(base_ip, prefix=24):
    """Generate random IP within given subnet"""
    ip_int = struct.unpack(">I", socket.inet_aton(base_ip))[0]
    mask = (0xffffffff << (32 - prefix)) & 0xffffffff
    host_bits = 0xffffffff ^ mask
    random_host = random.randint(0, host_bits)
    return socket.inet_ntoa(struct.pack(">I", (ip_int & mask) | random_host))

def get_local_ip():
    """Get local IP address"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()
