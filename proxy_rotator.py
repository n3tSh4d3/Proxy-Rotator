#!/usr/bin/env python3
"""
Proxy Rotator - Rotazione casuale di proxy con auto-aggiornamento
"""

import random
import time
import threading
import atexit
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.error
import socket
import re
from urllib.parse import urlparse
from datetime import datetime

class ProxyRotator:
    def __init__(self, proxy_list_file='proxy_list.txt', rotation_interval=9, 
                 auto_update=True, update_interval=300, proxy_sources_file='proxy_sources.txt',
                 validate_proxies=True, validation_timeout=5, test_url='http://httpbin.org/ip',
                 use_webshare=False, webshare_config='config.ini', cleanup_on_exit=True):
        """
        Inizializza il proxy rotator
        
        Args:
            proxy_list_file: File contenente la lista dei proxy (uno per riga)
            rotation_interval: Intervallo di rotazione in secondi (default: 9)
            auto_update: Abilita auto-aggiornamento della lista (default: True)
            update_interval: Intervallo di aggiornamento in secondi (default: 300 = 5 minuti)
            proxy_sources_file: File con URL sorgenti per scaricare proxy
            validate_proxies: Abilita validazione automatica dei proxy (default: True)
            validation_timeout: Timeout per test validazione in secondi (default: 5)
            test_url: URL per testare i proxy (default: http://httpbin.org/ip)
            use_webshare: Usa proxy da Webshare.io invece di proxy gratuiti (default: False)
            webshare_config: File di configurazione Webshare (default: config.ini)
            cleanup_on_exit: Cancella file proxy Webshare alla chiusura (default: True)
        """
        self.proxy_list_file = proxy_list_file
        self.rotation_interval = rotation_interval
        self.auto_update = auto_update
        self.update_interval = update_interval
        self.proxy_sources_file = proxy_sources_file
        self.validate_proxies = validate_proxies
        self.validation_timeout = validation_timeout
        self.test_url = test_url
        self.use_webshare = use_webshare
        self.webshare_config = webshare_config
        self.cleanup_on_exit = cleanup_on_exit
        self.proxy_list = []
        self.validated_proxies = []  # Lista dei proxy validati
        self.current_proxy = None
        self.lock = threading.Lock()
        self.last_update = None
        
        # Se usa Webshare, scarica i proxy all'avvio
        if self.use_webshare:
            self.fetch_webshare_proxies()
            # Registra cleanup alla chiusura
            if self.cleanup_on_exit:
                atexit.register(self.cleanup_webshare_file)
        
        self.load_proxy_list()
        
        # Se la lista è vuota e l'auto-update è attivo, scarica subito i proxy
        if self.auto_update and len(self.proxy_list) == 0 and not self.use_webshare:
            print("\n📥 Lista proxy vuota - Inizializzazione da sorgenti online...")
            self.update_from_sources()
        
        self.start_rotation()
        
        if self.auto_update and not self.use_webshare:
            self.start_auto_update()
    
    def load_proxy_list(self):
        """Carica la lista dei proxy dal file"""
        try:
            with open(self.proxy_list_file, 'r') as f:
                proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            need_selection = False
            with self.lock:
                old_count = len(self.proxy_list)
                self.proxy_list = proxies
                new_count = len(self.proxy_list)
                
                if new_count == 0:
                    print(f"⚠️  ATTENZIONE: Nessun proxy trovato in {self.proxy_list_file}")
                elif old_count == 0:
                    print(f"✓ Caricati {new_count} proxy da {self.proxy_list_file}")
                    need_selection = True
                else:
                    print(f"🔄 Lista aggiornata: {new_count} proxy (prima: {old_count})")
                    if self.current_proxy not in self.proxy_list and new_count > 0:
                        need_selection = True
                
                self.last_update = datetime.now()
            
            # Seleziona proxy fuori dal blocco lock per evitare deadlock
            if need_selection:
                self.select_random_proxy()
                
        except FileNotFoundError:
            print(f"❌ ERRORE: File {self.proxy_list_file} non trovato!")
            print("Creazione file di esempio...")
            self.create_example_proxy_file()
    
    def reload_proxy_list(self):
        """Ricarica la lista dei proxy dal file"""
        print(f"\n📥 Ricaricamento lista proxy da {self.proxy_list_file}...")
        self.load_proxy_list()
    
    def is_valid_proxy_format(self, proxy):
        """Valida il formato di un proxy"""
        # Formato: host:porta o http://host:porta
        patterns = [
            r'^https?://[\w\.-]+:\d+$',  # http://host:port
            r'^[\w\.-]+:\d+$',            # host:port
        ]
        return any(re.match(pattern, proxy) for pattern in patterns)
    
    def download_proxies_from_url(self, url):
        """Scarica lista di proxy da un URL"""
        try:
            print(f"  📡 Scaricamento da: {url}")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read().decode('utf-8', errors='ignore')
                
                # Estrai proxy dal contenuto
                proxies = []
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Prova a estrarre proxy in vari formati
                        if self.is_valid_proxy_format(line):
                            proxies.append(line)
                
                print(f"  ✓ Trovati {len(proxies)} proxy da {url}")
                return proxies
                
        except Exception as e:
            print(f"  ❌ Errore scaricando da {url}: {e}")
            return []
    
    def update_from_sources(self):
        """Aggiorna la lista proxy scaricando da sorgenti configurate"""
        try:
            with open(self.proxy_sources_file, 'r') as f:
                sources = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            if not sources:
                print(f"⚠️  Nessuna sorgente trovata in {self.proxy_sources_file}")
                return
            
            print(f"\n🌐 Aggiornamento da {len(sources)} sorgenti...")
            
            all_proxies = []
            for url in sources:
                proxies = self.download_proxies_from_url(url)
                all_proxies.extend(proxies)
            
            # Rimuovi duplicati
            all_proxies = list(set(all_proxies))
            
            if all_proxies:
                # Salva i nuovi proxy nel file
                with open(self.proxy_list_file, 'w') as f:
                    f.write(f"# Lista proxy aggiornata automaticamente il {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# Totale proxy: {len(all_proxies)}\n\n")
                    for proxy in all_proxies:
                        f.write(f"{proxy}\n")
                
                print(f"✓ Salvati {len(all_proxies)} proxy unici in {self.proxy_list_file}")
                
                # Valida i proxy se abilitato
                if self.validate_proxies:
                    all_proxies = self.validate_proxy_list(all_proxies)
                    
                    # Salva solo i proxy validati
                    if all_proxies:
                        with open(self.proxy_list_file, 'w') as f:
                            f.write(f"# Lista proxy validati automaticamente il {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                            f.write(f"# Totale proxy funzionanti: {len(all_proxies)}\n\n")
                            for proxy in all_proxies:
                                f.write(f"{proxy}\n")
                        print(f"✓ Salvati {len(all_proxies)} proxy VALIDATI in {self.proxy_list_file}")
                
                # Ricarica la lista
                self.load_proxy_list()
            else:
                print("⚠️  Nessun proxy scaricato dalle sorgenti")
                
        except FileNotFoundError:
            print(f"⚠️  File sorgenti {self.proxy_sources_file} non trovato")
            print("   Verrà usato solo il ricaricamento del file locale")
    
    def test_proxy(self, proxy):
        """Testa se un proxy funziona"""
        try:
            # Prepara il proxy
            if not proxy.startswith('http://') and not proxy.startswith('https://'):
                proxy_url = f'http://{proxy}'
            else:
                proxy_url = proxy
            
            proxy_handler = urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})
            opener = urllib.request.build_opener(proxy_handler)
            
            # Testa la connessione
            request = urllib.request.Request(self.test_url, headers={'User-Agent': 'Mozilla/5.0'})
            response = opener.open(request, timeout=self.validation_timeout)
            
            # Se arriviamo qui, il proxy funziona
            return response.getcode() == 200
            
        except Exception:
            return False
    
    def validate_proxy_list(self, proxies, max_workers=20):
        """Valida una lista di proxy in parallelo"""
        if not self.validate_proxies:
            return proxies
        
        print(f"\n🔍 Validazione di {len(proxies)} proxy (timeout: {self.validation_timeout}s)...")
        
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        valid_proxies = []
        tested = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Sottometti tutti i test
            future_to_proxy = {executor.submit(self.test_proxy, proxy): proxy for proxy in proxies}
            
            # Raccogli i risultati man mano che arrivano
            for future in as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                tested += 1
                
                try:
                    if future.result():
                        valid_proxies.append(proxy)
                        print(f"  ✓ [{tested}/{len(proxies)}] Valido: {proxy}")
                    else:
                        print(f"  ✗ [{tested}/{len(proxies)}] Non funziona: {proxy}", end='\r')
                except Exception:
                    print(f"  ✗ [{tested}/{len(proxies)}] Errore: {proxy}", end='\r')
        
        print(f"\n✓ Validazione completata: {len(valid_proxies)}/{len(proxies)} proxy funzionanti")
        return valid_proxies
    
    def fetch_webshare_proxies(self):
        """Scarica proxy da Webshare.io"""
        try:
            from webshare_fetcher import fetch_webshare_proxies
            
            # Determina il path del config.ini
            # Prova prima directory corrente (installazione manuale)
            # Poi /etc/proxy-rotator/ (pacchetto DEB)
            config_paths = [
                self.webshare_config,
                '/etc/proxy-rotator/config.ini'
            ]
            
            config_path = None
            for path in config_paths:
                if os.path.exists(path):
                    config_path = path
                    break
            
            if not config_path:
                print(f"❌ File di configurazione non trovato: {self.webshare_config}")
                print("⚠️  Nessun proxy Webshare scaricato, uso lista esistente")
                return
            
            print("\n🌐 Scaricamento proxy da Webshare.io...")
            count = fetch_webshare_proxies(config_path, self.proxy_list_file)
            
            if count > 0:
                print(f"✓ {count} proxy Webshare pronti all'uso")
            else:
                print("⚠️  Nessun proxy Webshare scaricato, uso lista esistente")
                
        except ImportError:
            print("❌ Errore: modulo webshare_fetcher non trovato")
        except Exception as e:
            print(f"❌ Errore scaricando proxy Webshare: {e}")
    
    def cleanup_webshare_file(self):
        """Cancella il file dei proxy Webshare alla chiusura"""
        if os.path.exists(self.proxy_list_file):
            try:
                os.remove(self.proxy_list_file)
                print(f"\n🗑️  File proxy Webshare cancellato: {self.proxy_list_file}")
            except Exception as e:
                print(f"\n⚠️  Errore cancellando file proxy: {e}")
    
    def auto_update_worker(self):
        """Thread worker per l'auto-aggiornamento periodico"""
        while True:
            time.sleep(self.update_interval)
            
            print(f"\n{'='*60}")
            print(f"🔄 Auto-aggiornamento lista proxy...")
            print(f"{'='*60}")
            
            # Prima prova ad aggiornare da sorgenti online
            try:
                self.update_from_sources()
            except Exception as e:
                print(f"⚠️  Errore aggiornamento da sorgenti: {e}")
            
            # Poi ricarica comunque il file locale (potrebbe essere stato modificato manualmente)
            self.reload_proxy_list()
            
            print(f"{'='*60}\n")
    
    def start_auto_update(self):
        """Avvia il thread di auto-aggiornamento"""
        update_thread = threading.Thread(target=self.auto_update_worker, daemon=True)
        update_thread.start()
        print(f"✓ Auto-aggiornamento abilitato (ogni {self.update_interval} secondi = {self.update_interval//60} minuti)")
    
    def create_example_proxy_file(self):
        """Crea un file di esempio con proxy"""
        example_proxies = [
            "# Formato: host:porta o http://host:porta",
            "# Questo file viene ricaricato automaticamente ogni pochi minuti",
            "# Puoi modificarlo mentre il programma è in esecuzione!",
            "",
            "# Esempio con proxy pubblici (potrebbero non funzionare):",
            "# 8.8.8.8:8080",
            "# 1.1.1.1:3128",
            "# http://proxy.example.com:8080",
            "",
            "# Aggiungi qui i tuoi proxy (uno per riga)"
        ]
        
        with open(self.proxy_list_file, 'w') as f:
            f.write('\n'.join(example_proxies))
        
        print(f"✓ Creato file di esempio: {self.proxy_list_file}")
        print("  Modifica il file aggiungendo i tuoi proxy (verrà ricaricato automaticamente)")
    
    def select_random_proxy(self):
        """Seleziona un proxy casuale dalla lista"""
        if not self.proxy_list:
            self.current_proxy = None
            return
        
        with self.lock:
            old_proxy = self.current_proxy
            self.current_proxy = random.choice(self.proxy_list)
            
            if old_proxy != self.current_proxy:
                print(f"🔄 Proxy cambiato: {self.current_proxy}")
            else:
                print(f"🔄 Proxy selezionato: {self.current_proxy}")
    
    def rotation_worker(self):
        """Thread worker per la rotazione automatica dei proxy"""
        while True:
            time.sleep(self.rotation_interval)
            self.select_random_proxy()
    
    def start_rotation(self):
        """Avvia il thread di rotazione automatica"""
        rotation_thread = threading.Thread(target=self.rotation_worker, daemon=True)
        rotation_thread.start()
        print(f"✓ Rotazione automatica avviata (ogni {self.rotation_interval} secondi)")
    
    def get_current_proxy(self):
        """Restituisce il proxy corrente"""
        with self.lock:
            return self.current_proxy


class ProxyHandler(BaseHTTPRequestHandler):
    """Handler per le richieste HTTP proxy"""
    
    def do_GET(self):
        """Gestisce le richieste GET"""
        self.proxy_request()
    
    def do_POST(self):
        """Gestisce le richieste POST"""
        self.proxy_request()
    
    def do_CONNECT(self):
        """Gestisce richieste CONNECT per HTTPS tunneling"""
        try:
            # Ottieni il proxy corrente
            current_proxy = self.server.rotator.current_proxy
            if not current_proxy:
                self.send_error(503, "Nessun proxy disponibile")
                return
            
            # Estrai host e porta dal path (formato: host:port)
            host, port = self.path.split(':')
            port = int(port)
            
            # Prepara il proxy upstream
            if not current_proxy.startswith('http://'):
                proxy_parts = current_proxy.split('@')
                if len(proxy_parts) == 2:
                    # Proxy con autenticazione: http://user:pass@host:port
                    auth, proxy_addr = proxy_parts
                    proxy_host, proxy_port = proxy_addr.split(':')
                else:
                    # Proxy senza autenticazione: host:port
                    proxy_host, proxy_port = current_proxy.split(':')
                proxy_port = int(proxy_port)
            else:
                # Formato completo: http://user:pass@host:port
                from urllib.parse import urlparse
                parsed = urlparse(current_proxy)
                proxy_host = parsed.hostname
                proxy_port = parsed.port or 8080
            
            # Connetti al proxy upstream
            proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            proxy_socket.settimeout(30)
            
            try:
                proxy_socket.connect((proxy_host, proxy_port))
                
                # Invia richiesta CONNECT al proxy upstream
                connect_request = f"CONNECT {host}:{port} HTTP/1.1\r\n"
                connect_request += f"Host: {host}:{port}\r\n"
                
                # Aggiungi autenticazione se presente
                if '@' in current_proxy:
                    from urllib.parse import urlparse
                    parsed = urlparse(current_proxy if current_proxy.startswith('http') else f'http://{current_proxy}')
                    if parsed.username and parsed.password:
                        import base64
                        credentials = f"{parsed.username}:{parsed.password}"
                        auth_header = base64.b64encode(credentials.encode()).decode()
                        connect_request += f"Proxy-Authorization: Basic {auth_header}\r\n"
                
                connect_request += "\r\n"
                proxy_socket.sendall(connect_request.encode())
                
                # Leggi risposta dal proxy upstream
                response = b""
                while b"\r\n\r\n" not in response:
                    chunk = proxy_socket.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                
                # Verifica che il proxy upstream abbia accettato la connessione
                if b"200" not in response.split(b"\r\n")[0]:
                    self.send_error(502, "Proxy upstream ha rifiutato la connessione CONNECT")
                    proxy_socket.close()
                    return
                
                # Invia risposta 200 al client
                self.send_response(200, "Connection Established")
                self.end_headers()
                
                # Inizia il tunneling bidirezionale
                self._tunnel_traffic(self.connection, proxy_socket)
                
            except socket.timeout:
                self.send_error(504, "Timeout connessione al proxy upstream")
            except Exception as e:
                self.send_error(502, f"Errore connessione proxy: {str(e)}")
            finally:
                proxy_socket.close()
                
        except Exception as e:
            try:
                self.send_error(500, f"Errore CONNECT: {str(e)}")
            except (BrokenPipeError, ConnectionResetError):
                pass
    
    def _tunnel_traffic(self, client_socket, proxy_socket):
        """Gestisce il tunneling bidirezionale tra client e proxy"""
        import select
        
        sockets = [client_socket, proxy_socket]
        timeout = 60
        
        try:
            while True:
                # Aspetta che uno dei socket sia pronto per leggere
                readable, _, exceptional = select.select(sockets, [], sockets, timeout)
                
                if exceptional:
                    break
                
                if not readable:
                    # Timeout
                    break
                
                for sock in readable:
                    # Leggi dati dal socket pronto
                    try:
                        data = sock.recv(8192)
                        if not data:
                            return
                        
                        # Invia i dati all'altro socket
                        if sock is client_socket:
                            proxy_socket.sendall(data)
                        else:
                            client_socket.sendall(data)
                    except:
                        return
        except:
            pass
    
    def proxy_request(self):
        """Inoltra la richiesta attraverso il proxy corrente"""
        current_proxy = self.server.rotator.get_current_proxy()
        
        if not current_proxy:
            self.send_error(503, "Nessun proxy disponibile")
            return
        
        try:
            # Prepara il proxy
            if not current_proxy.startswith('http://') and not current_proxy.startswith('https://'):
                proxy_url = f'http://{current_proxy}'
            else:
                proxy_url = current_proxy
            
            proxy_handler = urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})
            opener = urllib.request.build_opener(proxy_handler)
            
            # Prepara la richiesta
            headers = {key: val for key, val in self.headers.items()}
            
            # Effettua la richiesta
            request = urllib.request.Request(self.path, headers=headers)
            
            if self.command == 'POST':
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                request.data = post_data
            
            # Invia la richiesta attraverso il proxy
            response = opener.open(request, timeout=30)
            
            # Invia la risposta al client
            self.send_response(response.getcode())
            for header, value in response.headers.items():
                if header.lower() not in ['connection', 'keep-alive', 'proxy-connection']:
                    self.send_header(header, value)
            self.end_headers()
            
            self.wfile.write(response.read())
            
        except urllib.error.HTTPError as e:
            try:
                self.send_error(e.code, str(e))
            except (BrokenPipeError, ConnectionResetError):
                pass  # Client ha chiuso la connessione
        except urllib.error.URLError as e:
            try:
                self.send_error(502, f"Errore proxy: {str(e)}")
            except (BrokenPipeError, ConnectionResetError):
                pass  # Client ha chiuso la connessione
        except socket.timeout:
            try:
                self.send_error(504, "Gateway Timeout")
            except (BrokenPipeError, ConnectionResetError):
                pass  # Client ha chiuso la connessione
        except Exception as e:
            try:
                self.send_error(500, f"Errore interno: {str(e)}")
            except (BrokenPipeError, ConnectionResetError):
                pass  # Client ha chiuso la connessione
    
    def log_message(self, format, *args):
        """Override per personalizzare i log"""
        print(f"[{self.log_date_time_string()}] {format % args}")


class ProxyServer:
    """Server proxy con rotazione automatica"""
    
    def __init__(self, host='127.0.0.1', port=8888, proxy_list_file='proxy_list.txt', 
                 rotation_interval=9, auto_update=True, update_interval=300, 
                 proxy_sources_file='proxy_sources.txt', validate_proxies=True,
                 validation_timeout=5, test_url='http://httpbin.org/ip',
                 use_webshare=False, webshare_config='config.ini', cleanup_on_exit=True):
        """
        Inizializza il server proxy
        
        Args:
            host: Indirizzo di ascolto (default: 127.0.0.1)
            port: Porta di ascolto (default: 8888)
            proxy_list_file: File con la lista dei proxy
            rotation_interval: Intervallo di rotazione in secondi
            auto_update: Abilita auto-aggiornamento (default: True)
            update_interval: Intervallo aggiornamento in secondi (default: 300)
            proxy_sources_file: File con URL sorgenti proxy
            validate_proxies: Abilita validazione automatica (default: True)
            use_webshare: Usa proxy da Webshare.io (default: False)
            webshare_config: File configurazione Webshare (default: config.ini)
            cleanup_on_exit: Cancella file Webshare alla chiusura (default: True)
            validation_timeout: Timeout validazione in secondi (default: 5)
            test_url: URL per testare i proxy
        """
        self.host = host
        self.port = port
        self.rotator = ProxyRotator(
            proxy_list_file=proxy_list_file,
            rotation_interval=rotation_interval,
            auto_update=auto_update,
            update_interval=update_interval,
            proxy_sources_file=proxy_sources_file,
            validate_proxies=validate_proxies,
            validation_timeout=validation_timeout,
            test_url=test_url,
            use_webshare=use_webshare,
            webshare_config=webshare_config,
            cleanup_on_exit=cleanup_on_exit
        )
        self.server = None
    
    def start(self):
        """Avvia il server proxy"""
        try:
            self.server = HTTPServer((self.host, self.port), ProxyHandler)
            self.server.rotator = self.rotator
            
            print("\n" + "="*60)
            print(f"🚀 Proxy Rotator avviato su {self.host}:{self.port}")
            print(f"⏱️  Rotazione ogni {self.rotator.rotation_interval} secondi")
            if self.rotator.auto_update:
                print(f"🔄 Auto-aggiornamento: ATTIVO (ogni {self.rotator.update_interval//60} minuti)")
            else:
                print(f"🔄 Auto-aggiornamento: DISATTIVATO")
            if self.rotator.validate_proxies:
                print(f"✓ Validazione automatica: ATTIVA (timeout: {self.rotator.validation_timeout}s)")
            else:
                print(f"✗ Validazione automatica: DISATTIVATA")
            if self.rotator.use_webshare:
                print(f"💎 Proxy Webshare.io: ATTIVI")
            print("="*60)
            print("\nConfigura il tuo browser/applicazione per usare:")
            print(f"  HTTP Proxy: {self.host}:{self.port}")
            print("\nPremi CTRL+C per fermare il server\n")
            
            self.server.serve_forever()
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Server fermato dall'utente")
            self.stop()
        except Exception as e:
            print(f"\n❌ ERRORE: {e}")
            self.stop()
    
    def stop(self):
        """Ferma il server proxy"""
        if self.server:
            self.server.shutdown()
            print("✓ Server chiuso correttamente")


def main():
    """Funzione principale"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Proxy Rotator - Rotazione casuale di proxy con auto-aggiornamento',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  %(prog)s                                    # Usa impostazioni predefinite
  %(prog)s -f my_proxies.txt                  # Usa file proxy personalizzato
  %(prog)s -p 3128 -i 15                      # Porta 3128, rotazione ogni 15 secondi
  %(prog)s -H 0.0.0.0 -p 8080                 # Ascolta su tutte le interfacce
  %(prog)s --no-auto-update                   # Disabilita auto-aggiornamento
  %(prog)s -u 600                             # Aggiorna ogni 10 minuti
        """
    )
    
    parser.add_argument('-H', '--host', default='127.0.0.1',
                        help='Indirizzo di ascolto (default: 127.0.0.1)')
    parser.add_argument('-p', '--port', type=int, default=8888,
                        help='Porta di ascolto (default: 8888)')
    parser.add_argument('-f', '--file', default='proxy_list.txt',
                        help='File con la lista dei proxy (default: proxy_list.txt)')
    parser.add_argument('-i', '--interval', type=int, default=9,
                        help='Intervallo di rotazione in secondi (default: 9)')
    parser.add_argument('--no-auto-update', action='store_true',
                        help='Disabilita auto-aggiornamento della lista proxy')
    parser.add_argument('-u', '--update-interval', type=int, default=300,
                        help='Intervallo aggiornamento lista in secondi (default: 300 = 5 min)')
    parser.add_argument('-s', '--sources', default='proxy_sources.txt',
                        help='File con URL sorgenti proxy (default: proxy_sources.txt)')
    parser.add_argument('--no-validation', action='store_true',
                        help='Disabilita validazione automatica dei proxy')
    parser.add_argument('-t', '--validation-timeout', type=int, default=5,
                        help='Timeout validazione proxy in secondi (default: 5)')
    parser.add_argument('--test-url', default='http://httpbin.org/ip',
                        help='URL per testare i proxy (default: http://httpbin.org/ip)')
    parser.add_argument('--webshare', action='store_true',
                        help='Usa proxy da Webshare.io invece di proxy gratuiti')
    parser.add_argument('--webshare-config', default='config.ini',
                        help='File configurazione Webshare (default: config.ini)')
    parser.add_argument('--no-cleanup', action='store_true',
                        help='Non cancellare file proxy Webshare alla chiusura')
    
    args = parser.parse_args()
    
    # Avvia il server
    server = ProxyServer(
        host=args.host,
        port=args.port,
        proxy_list_file=args.file,
        rotation_interval=args.interval,
        auto_update=not args.no_auto_update,
        update_interval=args.update_interval,
        proxy_sources_file=args.sources,
        validate_proxies=not args.no_validation,
        validation_timeout=args.validation_timeout,
        test_url=args.test_url,
        use_webshare=args.webshare,
        webshare_config=args.webshare_config,
        cleanup_on_exit=not args.no_cleanup
    )
    
    server.start()


if __name__ == '__main__':
    main()
