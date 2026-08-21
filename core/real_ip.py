import json
import socket
import urllib.request
import ssl

CDN_RANGES = [
    "104.16.", "104.17.", "104.18.", "104.19.", "104.20.", "104.21.",
    "104.22.", "104.23.", "104.24.", "104.25.", "104.26.", "104.27.",
    "172.64.", "172.65.", "172.66.", "172.67.",
    "151.101.", "199.232.", "205.185.",
]

def get_subdomains(domain):
    """Fetch subdomains from crt.sh"""
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            data = json.loads(resp.read().decode())
            subdomains = set()
            for entry in data:
                name = entry.get("name_value", "")
                for sub in name.split("\n"):
                    sub = sub.strip().lower()
                    if sub and "*" not in sub:
                        subdomains.add(sub)
            return subdomains
    except Exception:
        return set()

def resolve_domain(hostname):
    """Resolve hostname to IPs"""
    try:
        return list(set(socket.gethostbyname_ex(hostname)[2]))
    except Exception:
        return []

def detect_real_ip(domain):
    """Detect real IP behind CDN"""
    domain = domain.lower().replace("https://", "").replace("http://", "").split("/")[0]
    print(f"[*] Detecting real IP for {domain}...")
    subs = get_subdomains(domain)
    subs.add(domain)

    candidates = []
    for sub in subs:
        ips = resolve_domain(sub)
        for ip in ips:
            if not any(ip.startswith(r) for r in CDN_RANGES):
                candidates.append((sub, ip))

    # Deduplicate by IP
    seen = set()
    unique = []
    for sub, ip in candidates:
        if ip not in seen:
            seen.add(ip)
            unique.append((sub, ip))
            print(f"[+] Found: {sub} -> {ip}")

    if unique:
        # Return first non-CDN IP
        return unique[0][1]
    return None
