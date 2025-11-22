# 🚀 Proxy Rotator con Webshare.io

Sistema completo di proxy rotation con supporto per proxy Webshare.io, gestione automatica, health check e rotazione intelligente.

## 📋 Indice

- [Caratteristiche](#-caratteristiche)
- [Requisiti](#-requisiti)
- [Installazione](#-installazione)
- [Configurazione](#-configurazione)
- [Utilizzo](#-utilizzo)
- [Avvio Automatico (systemd)](#-avvio-automatico-come-servizio-systemd)
- [Integrazione ZAP/Burp](#-integrazione-con-zapburp-suite)
- [Architettura](#-architettura)
- [Troubleshooting](#-troubleshooting)
- [FAQ](#-faq)
- [Licenza](#-licenza)

---

## ✨ Caratteristiche

### 🎯 Proxy Rotator
- ✅ Rotazione automatica proxy ogni 9 secondi (configurabile)
- ✅ Server HTTP proxy locale su porta 8888
- ✅ Supporto proxy Webshare.io con autenticazione
- ✅ Supporto HTTPS tramite CONNECT tunneling
- ✅ Validazione automatica proxy prima dell'uso
- ✅ Thread-safe e gestione errori robusta

### 🤖 C2 (Command & Control)
- ✅ Orchestrazione automatica di tutti i componenti
- ✅ Fetch periodico proxy da Webshare.io
- ✅ Health check continuo del proxy rotator
- ✅ Riavvio automatico in caso di crash
- ✅ Logging dettagliato con timestamp
- ✅ Graceful shutdown (CTRL+C)

### 🌐 Webshare Fetcher
- ✅ Download automatico proxy da Webshare.io
- ✅ Gestione paginazione API
- ✅ Rate limiting automatico
- ✅ Deduplicazione proxy
- ✅ Cleanup automatico alla chiusura

---

## 📦 Requisiti

### Sistema Operativo
- **Ubuntu 22.04** (o superiore)
- **Python 3.10+**

### Librerie Python
```bash
# Librerie standard Python (già incluse)
- threading
- subprocess
- argparse
- urllib
- socket
- datetime
- configparser

# Libreria esterna (da installare)
- requests
```

---

## 🔧 Installazione

Ci sono **due metodi** per installare Proxy Rotator:

### Metodo 1: Installazione Manuale (Consigliato per Sviluppatori)

Ideale per sviluppo, testing e personalizzazione.

#### 1️⃣ Clona il Repository

```bash
git clone https://github.com/n3tSh4d3/Proxy-Rotator.git
cd Proxy-Rotator
```

#### 2️⃣ Installa Dipendenze Python

```bash
# Aggiorna pip
python3 -m pip install --upgrade pip

# Installa requests
pip3 install requests
```

#### 3️⃣ Verifica Installazione

```bash
# Verifica Python
python3 --version  # Deve essere >= 3.10

# Verifica requests
python3 -c "import requests; print(requests.__version__)"
```

#### 4️⃣ Rendi Eseguibili gli Script

```bash
chmod +x proxy_c2.py
chmod +x proxy_rotator.py
chmod +x webshare_fetcher.py
```

---

### Metodo 2: Pacchetto DEB (Consigliato per Produzione)

Installazione professionale con servizio systemd automatico.

#### 📥 Opzione A: Download Release

```bash
# Download pacchetto .deb da GitHub Releases
wget https://github.com/n3tSh4d3/Proxy-Rotator/releases/download/v1.0.0/proxy-rotator_1.0.0_all.deb

# Installazione
sudo dpkg -i proxy-rotator_1.0.0_all.deb
sudo apt install -f  # Risolve dipendenze automaticamente
```

#### 🔨 Opzione B: Build da Sorgente

```bash
# Clona repository
git clone https://github.com/n3tSh4d3/Proxy-Rotator.git
cd Proxy-Rotator

# Build pacchetto DEB
./build-deb.sh

# Installazione
sudo dpkg -i dist/proxy-rotator_1.0.0_all.deb
sudo apt install -f
```

#### ⚙️ Configurazione Post-Installazione

```bash
# 1. Configura token Webshare
sudo nano /etc/proxy-rotator/config.ini
# Inserisci il tuo token Webshare

# 2. Avvia servizio
sudo systemctl start proxy-c2

# 3. Abilita avvio automatico
sudo systemctl enable proxy-c2

# 4. Verifica stato
sudo systemctl status proxy-c2

# 5. Visualizza log
sudo journalctl -u proxy-c2 -f
```

#### 📦 Comandi Disponibili (Solo Pacchetto DEB)

Dopo l'installazione del pacchetto DEB, avrai accesso a comandi globali:

```bash
# Orchestratore C2
proxy-c2 --help

# Proxy rotator standalone
proxy-rotator --help

# Fetcher Webshare
webshare-fetcher --help
```

#### 🗑️ Disinstallazione Pacchetto DEB

```bash
# Rimozione pacchetto (mantiene configurazione)
sudo apt remove proxy-rotator

# Rimozione completa (inclusa configurazione)
sudo apt purge proxy-rotator
```

---

### 📊 Confronto Metodi

| Caratteristica | Manuale | Pacchetto DEB |
|----------------|---------|---------------|
| **Installazione** | Manuale | Automatica |
| **Dipendenze** | Manuale | Automatiche (APT) |
| **Servizio systemd** | Manuale | Automatico |
| **Comandi globali** | ❌ | ✅ |
| **Avvio automatico** | Configurazione manuale | Integrato |
| **Aggiornamenti** | Git pull | `apt upgrade` |
| **Ideale per** | Sviluppo/Testing | Produzione |



## ⚙️ Configurazione

La configurazione varia in base al metodo di installazione utilizzato.

### 🔑 Ottenere il Token Webshare

Prima di configurare, ottieni il tuo token API:

1. **Vai su**: https://proxy.webshare.io/userapi/
2. **Login** al tuo account Webshare
3. **Copia il token** dalla sezione "API Key"
4. **Conserva il token** - lo userai nella configurazione

---

### Metodo 1: Configurazione Installazione Manuale

Se hai installato manualmente (senza pacchetto DEB):

#### 1️⃣ Modifica config.ini

```bash
# Apri il file di configurazione nella directory del progetto
nano config.ini
```

#### 2️⃣ Inserisci il Token

Modifica il file con il tuo token Webshare:

```ini
[webshare]
# Sostituisci con il tuo token da https://proxy.webshare.io/userapi/
token = [ inserisci il token webshare]

# Modalità: 'direct' o 'backbone'
mode = direct

# Numero di proxy per pagina (max 100)
page_size = 100

# Ritardo tra richieste API (secondi)
delay_between_requests = 0.4

# ID del piano (opzionale, lascia vuoto se non necessario)
plan_id = 

[general]
# File di output per i proxy Webshare
webshare_out = proxy_list.txt

# Cancella il file alla chiusura del programma
cleanup_on_exit = true
```

Salva con `CTRL+O`, `INVIO`, esci con `CTRL+X`.

#### 3️⃣ Verifica Configurazione

```bash
# Test fetch proxy
python3 webshare_fetcher.py

# Dovresti vedere:
# ✓ Salvati 500 proxy in proxy_list.txt
```

---

### Metodo 2: Configurazione Pacchetto DEB

Se hai installato tramite pacchetto DEB:

#### 1️⃣ Modifica File di Configurazione Sistema

```bash
# Il file di configurazione è in /etc/proxy-rotator/
sudo nano /etc/proxy-rotator/config.ini
```

#### 2️⃣ Inserisci il Token

Modifica il file con il tuo token Webshare:

```ini
[webshare]
# Sostituisci con il tuo token da https://proxy.webshare.io/userapi/
token = p36pkcv7xd4j191u5stkb1jj01uuruirium56rkp

# Modalità: 'direct' o 'backbone'
mode = direct

# Numero di proxy per pagina (max 100)
page_size = 100

# Ritardo tra richieste API (secondi)
delay_between_requests = 0.4

# ID del piano (opzionale)
plan_id = 

[general]
# File di output per i proxy Webshare (directory sistema)
webshare_out = /var/lib/proxy-rotator/proxy_list.txt

# Cancella il file alla chiusura del programma
cleanup_on_exit = true
```

Salva con `CTRL+O`, `INVIO`, esci con `CTRL+X`.

#### 3️⃣ Riavvia il Servizio

```bash
# Riavvia il servizio per applicare le modifiche
sudo systemctl restart proxy-c2

# Verifica che sia attivo
sudo systemctl status proxy-c2
```

#### 4️⃣ Verifica Configurazione

```bash
# Visualizza log in tempo reale
sudo journalctl -u proxy-c2 -f

# Dovresti vedere:
# 🌐 Scaricamento proxy da Webshare.io...
# ✓ Salvati 500 proxy in /var/lib/proxy-rotator/proxy_list.txt
```

---

### 🔐 Sicurezza Token

> [!WARNING]
> **Il token Webshare è sensibile!**
> - Non condividerlo pubblicamente
> - Non committarlo su Git
> - Non pubblicarlo su GitHub

Se usi Git con installazione manuale:

```bash
# Assicurati che config.ini sia in .gitignore
echo "config.ini" >> .gitignore
```

---

### 📋 Parametri Configurazione

| Parametro | Valori | Descrizione |
|-----------|--------|-------------|
| `token` | Stringa | Token API Webshare (obbligatorio) |
| `mode` | `direct` / `backbone` | Tipo di proxy Webshare |
| `page_size` | 1-100 | Proxy per pagina API |
| `delay_between_requests` | Secondi | Ritardo tra richieste API |
| `plan_id` | Numero | ID piano Webshare (opzionale) |
| `webshare_out` | Path | File output proxy |
| `cleanup_on_exit` | `true` / `false` | Cancella file alla chiusura |

---

### ❓ Troubleshooting Configurazione

#### Errore: "token' nella sezione [webshare]"

**Problema**: Token non configurato o file config.ini mancante

**Soluzione**:
- **Manuale**: Verifica che `config.ini` esista nella directory del progetto
- **DEB**: Verifica che `/etc/proxy-rotator/config.ini` esista

#### Errore: "HTTP 401 Unauthorized"

**Problema**: Token non valido o scaduto

**Soluzione**:
1. Verifica il token su https://proxy.webshare.io/userapi/
2. Copia il token corretto
3. Aggiorna `config.ini`
4. Riavvia il servizio (se DEB)

#### Errore: "HTTP 400 Bad Request"

**Problema**: Parametri configurazione errati

**Soluzione**:
- Verifica che `mode` sia `direct` o `backbone`
- Verifica che `page_size` sia tra 1 e 100
- Rimuovi spazi extra nel file config



## 🚀 Utilizzo

### Metodo Consigliato: C2 (Automatico)

Il **C2 (Command & Control)** gestisce automaticamente tutto il sistema:

```bash
# Avvio base (fetch proxy ogni ora)
python3 proxy_c2.py

# Fetch proxy ogni 30 minuti
python3 proxy_c2.py --fetch-interval 1800

# Fetch ogni 6 ore + health check ogni 2 minuti
python3 proxy_c2.py --fetch-interval 21600 --health-interval 120

# Config personalizzato
python3 proxy_c2.py --config my_config.ini --port 8888
```

#### Parametri C2

| Parametro | Default | Descrizione |
|-----------|---------|-------------|
| `--fetch-interval` | 3600 (1h) | Secondi tra fetch proxy Webshare |
| `--health-interval` | 60 (1min) | Secondi tra health check |
| `--config` | config.ini | File configurazione Webshare |
| `--port` | 8888 | Porta proxy rotator |

#### Output C2

```
============================================================
🚀 Proxy C2 - Avvio Sistema
============================================================
Configurazione:
  - Fetch intervallo: 3600s (1.0h)
  - Health check intervallo: 60s
  - Proxy porta: 8888
  - Config file: config.ini
============================================================
[2025-11-22 10:00:00] ℹ️  Avvio proxy rotator...
============================================================
🌐 Scaricamento proxy da Webshare.io...
  ✓ [Pagina 1] 100 proxy (totale: 100)
  ✓ [Pagina 2] 100 proxy (totale: 200)
  ...
✓ Salvati 500 proxy in proxy_list.txt
✓ Caricati 500 proxy da proxy_list.txt
🚀 Proxy Rotator avviato su 127.0.0.1:8888
⏱️  Rotazione ogni 9 secondi
💎 Proxy Webshare.io: ATTIVI
============================================================
[2025-11-22 10:00:15] ✅ Proxy rotator avviato (PID: 12345)
[2025-11-22 10:00:15] ℹ️  Worker fetch avviato (intervallo: 3600s)
[2025-11-22 10:00:15] ℹ️  Worker health check avviato (intervallo: 60s)
============================================================
✅ Sistema avviato con successo!
============================================================
Premi CTRL+C per fermare
🔄 Proxy cambiato: 82.22.232.219:8057
🔄 Proxy cambiato: 154.6.126.113:6084
...
```

### Metodo Manuale: Solo Proxy Rotator

Se vuoi controllare manualmente il sistema:

```bash
# Con proxy Webshare (consigliato)
python3 proxy_rotator.py --webshare

# Con proxy gratuiti (sconsigliato)
python3 proxy_rotator.py

# Parametri personalizzati
python3 proxy_rotator.py --webshare --interval 5 --port 8080
```

#### Parametri Proxy Rotator

| Parametro | Default | Descrizione |
|-----------|---------|-------------|
| `--webshare` | - | Usa proxy Webshare.io |
| `--interval` | 9 | Secondi tra rotazioni |
| `--port` | 8888 | Porta server proxy |
| `--host` | 127.0.0.1 | Indirizzo ascolto |
| `--no-validation` | - | Disabilita validazione proxy |
| `--validation-timeout` | 5 | Timeout validazione (secondi) |

---

## 🔧 Avvio Automatico come Servizio (systemd)

Per eseguire il Proxy C2 come servizio di sistema che si avvia automaticamente all'avvio di Ubuntu:

### 1️⃣ Crea il File di Servizio

Crea il file `/etc/systemd/system/proxy-c2.service`:

```bash
sudo nano /etc/systemd/system/proxy-c2.service
```

Inserisci il seguente contenuto (sostituisci `YOUR_USERNAME` con il tuo username):

```ini
[Unit]
Description=Proxy C2 - Webshare Proxy Rotator
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/Proxy-Rotator
ExecStart=/usr/bin/python3 /home/YOUR_USERNAME/Proxy-Rotator/proxy_c2.py --fetch-interval 3600 --health-interval 60
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Variabili ambiente (opzionale)
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

### 2️⃣ Configura i Permessi

```bash
# Imposta permessi corretti
sudo chmod 644 /etc/systemd/system/proxy-c2.service

# Ricarica systemd
sudo systemctl daemon-reload
```

### 3️⃣ Gestione del Servizio

```bash
# Avvia il servizio
sudo systemctl start proxy-c2

# Ferma il servizio
sudo systemctl stop proxy-c2

# Riavvia il servizio
sudo systemctl restart proxy-c2

# Abilita avvio automatico all'avvio del sistema
sudo systemctl enable proxy-c2

# Disabilita avvio automatico
sudo systemctl disable proxy-c2

# Verifica stato del servizio
sudo systemctl status proxy-c2
```

### 4️⃣ Visualizza i Log

```bash
# Log in tempo reale
sudo journalctl -u proxy-c2 -f

# Ultimi 100 log
sudo journalctl -u proxy-c2 -n 100

# Log di oggi
sudo journalctl -u proxy-c2 --since today

# Log con timestamp
sudo journalctl -u proxy-c2 --since "2025-11-22 10:00:00"
```

### 5️⃣ Verifica Funzionamento

```bash
# Verifica che il servizio sia attivo
sudo systemctl is-active proxy-c2

# Verifica che il proxy risponda
curl -x http://127.0.0.1:8888 http://httpbin.org/ip

# Verifica processi
ps aux | grep proxy
```

---

## 🔌 Integrazione con ZAP/Burp Suite

### Configurazione OWASP ZAP

1. **Avvia il C2**:
   ```bash
   python3 proxy_c2.py
   ```

2. **Configura ZAP**:
   - **Tools** → **Options** → **Connection**
   - **Use outgoing proxy server**: ✅
   - **Address**: `127.0.0.1`
   - **Port**: `8888`

3. **Test**:
   - Naviga su `https://httpbin.org/ip` tramite ZAP
   - L'IP mostrato sarà quello del proxy Webshare
   - Ogni 9 secondi l'IP cambierà automaticamente

### Configurazione Burp Suite

1. **User Options** → **Connections** → **Upstream Proxy Servers**
2. **Add**:
   - **Destination host**: `*`
   - **Proxy host**: `127.0.0.1`
   - **Proxy port**: `8888`

### 🛡️ Evitare Ban con BitNinja/WAF

Per evitare ban da WAF aggressivi:

1. **Riduci velocità scansione ZAP**:
   - Max connections: `2-3`
   - Delay: `2000ms` (2 secondi)
   - Threads: `1-2`

2. **Randomizza User-Agent**:
   ```
   Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
   ```

3. **Rotazione più frequente**:
   ```bash
   python3 proxy_c2.py --fetch-interval 1800  # 30 minuti
   ```

4. **Modalità Stealth**:
   - Usa **Protected Mode** in ZAP
   - Evita Active Scan aggressivo
   - Preferisci Manual Explore

---

## 🏗️ Architettura

```
┌─────────────────────────────────────────────┐
│           Proxy C2 (Orchestratore)          │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  Thread 1: Fetch Worker              │  │
│  │  - Fetch immediato all'avvio         │  │
│  │  - Fetch periodico ogni N secondi    │  │
│  │  - Esegue webshare_fetcher.py        │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  Thread 2: Health Check Worker       │  │
│  │  - Verifica processo vivo            │  │
│  │  - Test connettività proxy           │  │
│  │  - Riavvio automatico se fallisce    │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  Processo: Proxy Rotator             │  │
│  │  - Server HTTP su porta 8888         │  │
│  │  - Rotazione proxy ogni 9s           │  │
│  │  - Supporto HTTP/HTTPS (CONNECT)     │  │
│  └──────────────────────────────────────┘  │
│                                             │
└─────────────────────────────────────────────┘
                     ↓
        ┌────────────────────────┐
        │   Webshare.io API      │
        │   500 proxy premium    │
        └────────────────────────┘
```

### Flusso Traffico

```
Browser/ZAP → Proxy Rotator (8888) → Webshare Proxy → Internet
              ↑
              Rotazione ogni 9s
              Health check ogni 60s
```

---

## 🐛 Troubleshooting

### ❌ Errore: "Address already in use"

**Problema**: Porta 8888 già occupata

**Soluzione**:
```bash
# Trova processo sulla porta 8888
sudo lsof -i :8888

# Termina processo
kill -9 <PID>

# Oppure usa porta diversa
python3 proxy_c2.py --port 9999
```

### ❌ Errore: "No module named 'requests'"

**Problema**: Libreria requests non installata

**Soluzione**:
```bash
pip3 install requests
```

### ❌ Errore: "token' nella sezione [webshare]"

**Problema**: Token Webshare non configurato

**Soluzione**:
1. Ottieni token da https://proxy.webshare.io/userapi/
2. Modifica `config.ini`:
   ```ini
   [webshare]
   token = IL_TUO_TOKEN
   ```

### ⚠️ Warning: "Health check fallito"

**Problema**: Proxy rotator non risponde

**Soluzione**:
- Il C2 riavvierà automaticamente dopo 3 fallimenti
- Verifica log per errori
- Controlla connettività internet

---

## ❓ FAQ

### Q: Quanti proxy posso ottenere da Webshare?
**A**: Dipende dal tuo piano. Il fetcher scarica automaticamente tutti i proxy disponibili.

### Q: Posso usare proxy gratuiti invece di Webshare?
**A**: Sì, ma **sconsigliato**. I proxy gratuiti sono inaffidabili e spesso non funzionano. Usa `python3 proxy_rotator.py` senza `--webshare`.

### Q: Come faccio a fermare il sistema?
**A**: Premi **CTRL+C**. Il C2 farà graceful shutdown di tutti i componenti.

### Q: Il file proxy_list.txt viene cancellato alla chiusura?
**A**: Sì, per sicurezza. Puoi disabilitare con `--no-cleanup` o modificando `cleanup_on_exit = false` in config.ini.

### Q: Posso usare il proxy rotator senza C2?
**A**: Sì, ma dovrai gestire manualmente fetch e restart. Consigliato usare C2.

### Q: Quanto spesso vengono aggiornati i proxy?
**A**: Default ogni ora. Configurabile con `--fetch-interval`.

### Q: Il proxy rotator funziona con HTTPS?
**A**: Sì! Supporta HTTPS tramite CONNECT tunneling.

### Q: Come verifico che il proxy funzioni?
**A**: 
```bash
# Test HTTP
curl -x http://127.0.0.1:8888 http://httpbin.org/ip

# Test HTTPS
curl -x http://127.0.0.1:8888 https://httpbin.org/ip
```

---

## 📝 File del Progetto

```
Proxy-Rotator/
├── proxy_c2.py              # C2 orchestratore (AVVIA QUESTO)
├── proxy_rotator.py         # Server proxy con rotazione
├── webshare_fetcher.py      # Fetcher proxy Webshare
├── config.ini               # Configurazione Webshare
├── proxy_list.txt           # Lista proxy (auto-generato)
└── README.md                # Questa documentazione
```

---

## 🎯 Quick Start

```bash
# 1. Clona repository
git clone https://github.com/n3tSh4d3/Proxy-Rotator.git
cd Proxy-Rotator

# 2. Installa dipendenze
pip3 install requests

# 3. Configura token in config.ini
nano config.ini  # Inserisci il tuo token Webshare

# 4. Avvia il sistema
python3 proxy_c2.py

# 5. Configura ZAP/Burp
# Proxy: 127.0.0.1:8888

# 6. Profit! 🎉
```

---

## 📄 Licenza

**Copyright © 2025 CONDRò Adriano**

Questo software può essere liberamente copiato e distribuito, ma la licenza e i diritti d'autore rimangono di proprietà esclusiva di **CONDRò Adriano**.

### Termini di Utilizzo

✅ **Permesso di**:
- Copiare il software
- Distribuire il software
- Utilizzare il software per scopi personali e commerciali
- Modificare il software per uso personale

❌ **Non è permesso**:
- Rimuovere o modificare le informazioni sul copyright
- Rivendicare la proprietà del software originale
- Distribuire versioni modificate senza citare l'autore originale

### Disclaimer

Questo progetto è fornito "as-is" senza garanzie di alcun tipo, esplicite o implicite. L'autore non si assume alcuna responsabilità per danni derivanti dall'uso di questo software.

---

**Buon proxy rotation! 🚀**
