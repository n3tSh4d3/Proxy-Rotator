#!/usr/bin/env python3
"""
webshare_fetcher.py
Scarica proxy da Webshare.io per il Proxy Rotator
"""
import os
import sys
import time
import requests
import urllib.parse
import configparser
import json

def fetch_webshare_proxies(config_file="config.ini", output_file="webshare_proxies.txt"):
    """
    Scarica proxy da Webshare e li salva in un file
    
    Args:
        config_file: Path al file di configurazione
        output_file: Path dove salvare i proxy
    
    Returns:
        Numero di proxy scaricati
    """
    if not os.path.exists(config_file):
        print(f"❌ File di configurazione non trovato: {config_file}", file=sys.stderr)
        return 0
    
    cfg = configparser.ConfigParser()
    cfg.read(config_file)
    
    # Leggi configurazione Webshare
    try:
        token = cfg.get("webshare", "token")
    except Exception:
        print("❌ Errore: imposta 'token' nella sezione [webshare] del config.ini", file=sys.stderr)
        return 0
    
    mode = cfg.get("webshare", "mode", fallback="direct")
    page_size = cfg.getint("webshare", "page_size", fallback=100)
    sleep_sec = cfg.getfloat("webshare", "delay_between_requests", fallback=0.35)
    plan_id = cfg.get("webshare", "plan_id", fallback="").strip()
    
    base_url = "https://proxy.webshare.io/api/v2/proxy/list/"
    headers = {"Authorization": f"Token {token}"}
    session = requests.Session()
    session.headers.update(headers)
    
    # Fetch tutti i proxy
    params = {"mode": mode, "page": 1, "page_size": page_size}
    if plan_id:
        params["plan_id"] = plan_id
    
    url = base_url + "?" + urllib.parse.urlencode(params)
    results = []
    page = 1
    
    print(f"\n📡 Scaricamento proxy da Webshare.io (mode={mode})...")
    
    while url:
        try:
            r = session.get(url, timeout=30)
            
            if r.status_code == 429:
                print("⚠️  Rate limit: attendo 60s...")
                time.sleep(60)
                continue
            
            if r.status_code == 400:
                print(f"❌ HTTP 400: {r.text}", file=sys.stderr)
                print("💡 Verifica 'mode' e 'plan_id' nel config.ini", file=sys.stderr)
                return 0
            
            if not r.ok:
                print(f"❌ Errore HTTP {r.status_code}: {r.text}", file=sys.stderr)
                return 0
            
            data = r.json()
            page_items = data.get("results", [])
            print(f"  ✓ [Pagina {page}] {len(page_items)} proxy (totale: {len(results) + len(page_items)})")
            results.extend(page_items)
            
            next_url = data.get("next")
            if next_url:
                next_url = urllib.parse.urljoin(base_url, next_url)
            url = next_url
            page += 1
            time.sleep(sleep_sec)
            
        except Exception as e:
            print(f"❌ Errore durante il fetch: {e}", file=sys.stderr)
            break
    
    # Normalizza i proxy nel formato corretto
    proxies = []
    for item in results:
        ip = item.get("proxy_address")
        port = item.get("port")
        user = item.get("username")
        pwd = item.get("password")
        
        if ip and port and user and pwd:
            # Formato: http://user:pass@host:port
            proxy = f"http://{user}:{pwd}@{ip}:{port}"
            proxies.append(proxy)
    
    # Rimuovi duplicati
    proxies = list(set(proxies))
    
    # Salva nel file
    os.makedirs(os.path.dirname(os.path.abspath(output_file)) if os.path.dirname(output_file) else ".", exist_ok=True)
    with open(output_file, "w") as f:
        f.write(f"# Proxy Webshare.io scaricati il {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Totale: {len(proxies)} proxy\n\n")
        for proxy in proxies:
            f.write(f"{proxy}\n")
    
    print(f"✓ Salvati {len(proxies)} proxy in {output_file}")
    return len(proxies)


if __name__ == "__main__":
    # Test standalone
    import argparse
    parser = argparse.ArgumentParser(description="Scarica proxy da Webshare.io")
    parser.add_argument("-c", "--config", default="config.ini", help="File di configurazione")
    parser.add_argument("-o", "--output", default="webshare_proxies.txt", help="File di output")
    args = parser.parse_args()
    
    count = fetch_webshare_proxies(args.config, args.output)
    if count > 0:
        print(f"\n✅ Completato! {count} proxy pronti all'uso.")
    else:
        print("\n❌ Nessun proxy scaricato.")
        sys.exit(1)
