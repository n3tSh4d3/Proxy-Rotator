#!/usr/bin/env python3
"""
Proxy C2 (Command & Control)
Orchestratore per gestire webshare_fetcher e proxy_rotator
"""

import subprocess
import time
import argparse
import sys
import os
import signal
import requests
from datetime import datetime
from threading import Thread, Event

class ProxyC2:
    def __init__(self, fetch_interval=3600, config_file='config.ini', 
                 proxy_port=8888, health_check_interval=60):
        """
        Inizializza il C2
        
        Args:
            fetch_interval: Intervallo in secondi per aggiornare i proxy (default: 3600 = 1 ora)
            config_file: File di configurazione Webshare
            proxy_port: Porta del proxy rotator (default: 8888)
            health_check_interval: Intervallo health check in secondi (default: 60)
        """
        self.fetch_interval = fetch_interval
        self.config_file = config_file
        self.proxy_port = proxy_port
        self.health_check_interval = health_check_interval
        
        self.rotator_process = None
        self.stop_event = Event()
        self.fetcher_thread = None
        self.health_thread = None
        
        # Registra handler per SIGINT/SIGTERM
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Gestisce segnali di terminazione"""
        print(f"\n⚠️  Ricevuto segnale {signum} - Arresto in corso...")
        self.stop()
        sys.exit(0)
    
    def log(self, message, level="INFO"):
        """Log con timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️ ",
            "DEBUG": "🔍"
        }.get(level, "")
        print(f"[{timestamp}] {prefix} {message}")
    
    def fetch_proxies(self):
        """Esegue webshare_fetcher per scaricare nuovi proxy"""
        self.log("Avvio fetch proxy da Webshare...", "INFO")
        
        try:
            result = subprocess.run(
                ['python3', 'webshare_fetcher.py', '-c', self.config_file],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                # Estrai numero di proxy dal output
                output = result.stdout
                if "proxy pronti all'uso" in output or "Completato" in output:
                    self.log("Fetch proxy completato con successo", "SUCCESS")
                    return True
                else:
                    self.log(f"Fetch completato ma output inaspettato: {output}", "WARNING")
                    return True
            else:
                self.log(f"Errore fetch proxy: {result.stderr}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("Timeout durante fetch proxy (>120s)", "ERROR")
            return False
        except Exception as e:
            self.log(f"Eccezione durante fetch proxy: {e}", "ERROR")
            return False
    
    def fetch_worker(self):
        """Thread worker per fetch periodico dei proxy"""
        self.log(f"Worker fetch avviato (intervallo: {self.fetch_interval}s)", "INFO")
        
        # Primo fetch immediato
        self.fetch_proxies()
        
        # Fetch periodici
        while not self.stop_event.is_set():
            # Attendi intervallo (con check ogni secondo per stop rapido)
            for _ in range(self.fetch_interval):
                if self.stop_event.is_set():
                    break
                time.sleep(1)
            
            if not self.stop_event.is_set():
                self.fetch_proxies()
        
        self.log("Worker fetch terminato", "INFO")
    
    def start_rotator(self):
        """Avvia il proxy rotator"""
        self.log("Avvio proxy rotator...", "INFO")
        self.log("=" * 60, "INFO")
        
        try:
            # Avvia proxy_rotator.py con webshare - lascia stdout/stderr visibili
            self.rotator_process = subprocess.Popen(
                ['python3', 'proxy_rotator.py', '--webshare']
            )
            
            # Attendi un po' per verificare che non crashi immediatamente
            time.sleep(3)
            
            if self.rotator_process.poll() is None:
                self.log("=" * 60, "INFO")
                self.log(f"✅ Proxy rotator avviato (PID: {self.rotator_process.pid})", "SUCCESS")
                return True
            else:
                self.log(f"Proxy rotator crashato all'avvio", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Errore avvio proxy rotator: {e}", "ERROR")
            return False
    
    def check_rotator_health(self):
        """Verifica che il proxy rotator sia funzionante"""
        # 1. Verifica che il processo sia vivo
        if self.rotator_process is None or self.rotator_process.poll() is not None:
            return False
        
        # 2. Verifica che la porta sia in ascolto
        try:
            response = requests.get(
                'http://httpbin.org/ip',
                proxies={'http': f'http://127.0.0.1:{self.proxy_port}'},
                timeout=10
            )
            
            if response.status_code == 200:
                return True
            else:
                self.log(f"Health check fallito: HTTP {response.status_code}", "WARNING")
                return False
                
        except requests.exceptions.ProxyError:
            self.log("Health check fallito: errore proxy", "WARNING")
            return False
        except requests.exceptions.Timeout:
            self.log("Health check fallito: timeout", "WARNING")
            return False
        except Exception as e:
            self.log(f"Health check fallito: {e}", "WARNING")
            return False
    
    def health_check_worker(self):
        """Thread worker per health check periodico"""
        self.log(f"Worker health check avviato (intervallo: {self.health_check_interval}s)", "INFO")
        
        consecutive_failures = 0
        max_failures = 3
        
        # Attendi che il rotator si avvii
        time.sleep(10)
        
        while not self.stop_event.is_set():
            if self.check_rotator_health():
                if consecutive_failures > 0:
                    self.log("Proxy rotator recuperato", "SUCCESS")
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                self.log(f"Health check fallito ({consecutive_failures}/{max_failures})", "WARNING")
                
                if consecutive_failures >= max_failures:
                    self.log("Troppi health check falliti - Riavvio proxy rotator", "ERROR")
                    self.restart_rotator()
                    consecutive_failures = 0
            
            # Attendi intervallo
            for _ in range(self.health_check_interval):
                if self.stop_event.is_set():
                    break
                time.sleep(1)
        
        self.log("Worker health check terminato", "INFO")
    
    def restart_rotator(self):
        """Riavvia il proxy rotator"""
        self.log("Riavvio proxy rotator in corso...", "INFO")
        
        # Termina processo esistente
        if self.rotator_process and self.rotator_process.poll() is None:
            self.rotator_process.terminate()
            try:
                self.rotator_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.rotator_process.kill()
                self.rotator_process.wait()
        
        # Attendi un po'
        time.sleep(2)
        
        # Riavvia
        if self.start_rotator():
            self.log("Proxy rotator riavviato con successo", "SUCCESS")
        else:
            self.log("Fallito riavvio proxy rotator", "ERROR")
    
    def start(self):
        """Avvia il C2"""
        self.log("=" * 60, "INFO")
        self.log("🚀 Proxy C2 - Avvio Sistema", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"Configurazione:", "INFO")
        self.log(f"  - Fetch intervallo: {self.fetch_interval}s ({self.fetch_interval/3600:.1f}h)", "INFO")
        self.log(f"  - Health check intervallo: {self.health_check_interval}s", "INFO")
        self.log(f"  - Proxy porta: {self.proxy_port}", "INFO")
        self.log(f"  - Config file: {self.config_file}", "INFO")
        self.log("=" * 60, "INFO")
        
        # Verifica che i file necessari esistano
        if not os.path.exists('webshare_fetcher.py'):
            self.log("File webshare_fetcher.py non trovato!", "ERROR")
            return False
        
        if not os.path.exists('proxy_rotator.py'):
            self.log("File proxy_rotator.py non trovato!", "ERROR")
            return False
        
        if not os.path.exists(self.config_file):
            self.log(f"File config {self.config_file} non trovato!", "ERROR")
            return False
        
        # Avvia proxy rotator
        if not self.start_rotator():
            self.log("Impossibile avviare proxy rotator - Uscita", "ERROR")
            return False
        
        # Avvia thread fetch periodico
        self.fetcher_thread = Thread(target=self.fetch_worker, daemon=True)
        self.fetcher_thread.start()
        
        # Avvia thread health check
        self.health_thread = Thread(target=self.health_check_worker, daemon=True)
        self.health_thread.start()
        
        self.log("=" * 60, "INFO")
        self.log("✅ Sistema avviato con successo!", "SUCCESS")
        self.log("=" * 60, "INFO")
        self.log("Premi CTRL+C per fermare", "INFO")
        
        # Loop principale - attendi stop
        try:
            while not self.stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        
        return True
    
    def stop(self):
        """Ferma il C2"""
        self.log("Arresto sistema in corso...", "INFO")
        
        # Segnala stop ai thread
        self.stop_event.set()
        
        # Termina proxy rotator
        if self.rotator_process and self.rotator_process.poll() is None:
            self.log("Terminazione proxy rotator...", "INFO")
            self.rotator_process.terminate()
            try:
                self.rotator_process.wait(timeout=10)
                self.log("Proxy rotator terminato", "SUCCESS")
            except subprocess.TimeoutExpired:
                self.log("Timeout terminazione - Invio SIGKILL", "WARNING")
                self.rotator_process.kill()
                self.rotator_process.wait()
        
        # Attendi thread
        if self.fetcher_thread and self.fetcher_thread.is_alive():
            self.fetcher_thread.join(timeout=5)
        
        if self.health_thread and self.health_thread.is_alive():
            self.health_thread.join(timeout=5)
        
        self.log("=" * 60, "INFO")
        self.log("✅ Sistema arrestato correttamente", "SUCCESS")
        self.log("=" * 60, "INFO")


def main():
    parser = argparse.ArgumentParser(
        description='Proxy C2 - Orchestratore per webshare_fetcher e proxy_rotator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  # Avvia con fetch ogni ora (default)
  python3 proxy_c2.py
  
  # Fetch ogni 30 minuti
  python3 proxy_c2.py --fetch-interval 1800
  
  # Fetch ogni 6 ore con health check ogni 2 minuti
  python3 proxy_c2.py --fetch-interval 21600 --health-interval 120
  
  # Usa config personalizzato
  python3 proxy_c2.py --config my_config.ini
        """
    )
    
    parser.add_argument(
        '--fetch-interval',
        type=int,
        default=3600,
        help='Intervallo in secondi per fetch proxy (default: 3600 = 1 ora)'
    )
    
    parser.add_argument(
        '--health-interval',
        type=int,
        default=60,
        help='Intervallo in secondi per health check (default: 60)'
    )
    
    parser.add_argument(
        '--config',
        default='config.ini',
        help='File di configurazione Webshare (default: config.ini)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8888,
        help='Porta del proxy rotator (default: 8888)'
    )
    
    args = parser.parse_args()
    
    # Crea e avvia C2
    c2 = ProxyC2(
        fetch_interval=args.fetch_interval,
        config_file=args.config,
        proxy_port=args.port,
        health_check_interval=args.health_interval
    )
    
    c2.start()


if __name__ == '__main__':
    main()
