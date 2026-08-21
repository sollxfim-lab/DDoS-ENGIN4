```markdown
# DDoS Toolkit

Professional multi-vector DDoS testing toolkit written in Python 3. Supports raw socket attacks, IP spoofing, proxy-based HTTP flood, Slowloris, and multiple amplification methods.

## Features

- **UDP Flood** — 65KB payload, multi-threaded
- **SYN Flood** — half-open TCP connections, IP spoofing supported
- **ICMP Flood** — ping flood with raw socket
- **TCP Flood** — raw TCP packets, random flags
- **HTTP Flood** — proxy support, user-agent rotation, X-Forwarded-For spoofing
- **Slowloris** — connection pool, keep-alive, proxy support
- **DNS Amplification** — ANY query, multiple public DNS servers
- **NTP Amplification** — monlist request, multiple NTP servers
- **Memcached Amplification** — stats query, uses all IPs from `all_ip.txt`
- **IP Spoofing** — raw socket with custom IP header
- **Real IP Detection** — find origin IP behind CDN via crt.sh subdomain enumeration
- **Proxy Scraper** — scrapes 24+ free proxy sources
- **User-Agent Scraper** — downloads fresh user-agent list

## Project Structure

```
ddos_toolkit/
├── app.py                          # main CLI application
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
│   └── memcached_amp.py
└── all-ipv4-ClassC-192,168/
    └── all_ip.txt                  # 65,536 IPs for Memcached amplification
```

## Requirements

- Python 3.8+
- Linux recommended
- Root/admin privileges for raw socket and IP spoofing
- Dependencies listed in `requirements.txt`

## Installation

```bash
cd ddos_toolkit
pip install -r requirements.txt
```

`requirements.txt` content:

```
scapy==2.5.0
requests==2.31.0
dnspython==2.4.2
```

## Usage

### Scrape Proxies

Scrape proxies from 24+ sources and save to `proxy.txt` and `proxt.txt`.

```bash
python3 app.py --scrape-proxies
```

### Scrape User-Agents

Scrape user-agent list and save to `ua.txt`.

```bash
python3 app.py --scrape-ua
```

### Run Attack

Basic syntax:

```bash
sudo python3 app.py --target <target> --port <port> --method <method> --threads <threads> --duration <seconds> [options]
```

### Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--target` | Target IP or domain | required |
| `--port` | Target port | `80` |
| `--method` | Attack method | required |
| `--threads` | Number of threads | `100` |
| `--duration` | Attack duration in seconds | `60` |
| `--spoof` | Enable IP spoofing (raw socket, requires root) | off |
| `--real-ip` | Detect real IP behind CDN before attack | off |
| `--proxy` | Use proxies from `proxy.txt` for HTTP/Slowloris | off |
| `--proxy-file` | Use custom proxy file | `proxy.txt` |
| `--ua-file` | Use custom user-agent file for HTTP flood | `ua.txt` |
| `--scrape-proxies` | Scrape proxies and exit | — |
| `--scrape-ua` | Scrape user-agents and exit | — |

### Attack Methods

| Method | Description | Requires root |
|--------|-------------|---------------|
| `udp` | UDP flood | yes (spoof) |
| `syn` | SYN flood | yes (spoof) |
| `icmp` | ICMP flood | yes |
| `tcp` | TCP flood with random flags | yes |
| `http` | HTTP flood | no |
| `slowloris` | Slowloris connection exhaustion | no |
| `dns` | DNS amplification | no |
| `ntp` | NTP amplification | no |
| `memcached` | Memcached amplification using `all_ip.txt` | no |

### Examples

**SYN flood with IP spoofing**

```bash
sudo python3 app.py --target 192.168.1.10 --port 80 --method syn --threads 300 --duration 30 --spoof
```

**HTTP flood using scraped proxies**

```bash
python3 app.py --scrape-proxies
python3 app.py --target example.com --port 80 --method http --threads 200 --duration 60 --proxy
```

**Slowloris with proxies**

```bash
python3 app.py --target example.com --port 80 --method slowloris --threads 150 --duration 120 --proxy
```

**Memcached amplification using all IPs from `all_ip.txt`**

```bash
python3 app.py --target 192.168.1.10 --port 11211 --method memcached --threads 500 --duration 60
```

**Detect real IP behind CDN then attack**

```bash
sudo python3 app.py --target example.com --port 443 --method syn --threads 200 --duration 30 --real-ip --spoof
```

## Notes

- IP spoofing requires raw socket access. Run with `sudo` or as root.
- `all_ip.txt` must exist and contain one IP per line. The Memcached module loads all IPs from this file.
- Proxy scraper writes to both `proxy.txt` and `proxt.txt`.
- User-agent scraper writes to `ua.txt`.
- For maximum performance, adjust `--threads` based on available system resources.
- Attack duration can be interrupted with `Ctrl+C`; threads will stop gracefully.
- HTTP and Slowloris attacks can work without root when not using raw sockets.
- Ensure the target and port are correct before starting an attack.
```
