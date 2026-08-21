import os
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

PROXY_SOURCES = [
    "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&proxy_format=ipport&format=text&timeout=20000",
    "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/http.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/https.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/http/http.txt",
    "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/https.txt",
    "https://raw.githubusercontent.com/berkay-digital/Proxy-Scraper/main/proxies.txt",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/https.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/http.txt",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
    "https://raw.githubusercontent.com/elliottophellia/proxylist/master/results/http/global/http_checked.txt",
    "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/https/https.txt",
    "https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=5000",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/http.txt",
]

UA_URL = "https://raw.githubusercontent.com/rafael453322/PROXYDT/main/proxy.json.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
}

def _fetch_text(url, timeout=15):
    try:
        r = requests.get(url, timeout=timeout, headers=HEADERS)
        r.raise_for_status()
        return r.text
    except Exception:
        return ""

def scrape_proxies(output_files=("proxy.txt", "proxt.txt")):
    """Scrape proxies dari banyak sumber, deduplikasi, simpan ke file."""
    proxies = set()

    def _scrape_source(source):
        text = _fetch_text(source)
        if not text:
            return []
        lines = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]
        pattern = re.compile(r"^\d{1,3}(\.\d{1,3}){3}:\d{2,5}$")
        return [p for p in lines if pattern.match(p)]

    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(_scrape_source, src): src for src in PROXY_SOURCES}
        for fut in as_completed(futures):
            proxies.update(fut.result())

    unique = sorted(proxies)

    for fname in output_files:
        try:
            with open(fname, "w", encoding="utf-8") as f:
                f.write("\n".join(unique))
        except Exception:
            pass

    return unique

def scrape_user_agents(output_file="ua.txt"):
    """Scrape user-agent list dari sumber dan simpan ke file."""
    text = _fetch_text(UA_URL)
    if text:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception:
            pass
    return text
