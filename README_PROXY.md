# 🚀 Proxy Rotator con Webshare.io

Sistema completo di proxy rotation con supporto per proxy Webshare.io, gestione automatica, health check e rotazione intelligente.

## 📋 Indice

- [Caratteristiche](#-caratteristiche)
- [Requisiti](#-requisiti)
- [Installazione](#-installazione)
- [Configurazione](#-configurazione)
- [Utilizzo](#-utilizzo)
- [Architettura](#-architettura)
- [Troubleshooting](#-troubleshooting)
- [FAQ](#-faq)

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

## � Requisiti

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

### 1️⃣ Clona/Scarica il Progetto

```bash
cd ~/Documents/antigravity_project/project1
```

### 2️⃣ Installa Dipendenze Python

```bash
# Aggiorna pip
python3 -m pip install --upgrade pip

# Installa requests
pip3 install requests
```

### 3️⃣ Verifica Installazione

```bash
# Verifica Python
python3 --version  # Deve essere >= 3.10

# Verifica requests
python3 -c "import requests; print(requests.__version__)"
```

### 4️⃣ Rendi Eseguibili gli Script

```bash
chmod +x proxy_c2.py
chmod +x proxy_rotator.py
chmod +x webshare_fetcher.py
```

---

## ⚙️ Configurazione

### 1️⃣ Configura Webshare.io

Modifica `config.ini` con il tuo token Webshare:

```ini
[webshare]
# Ottieni il token da: https://proxy.webshare.io/userapi/
token = IL_TUO_TOKEN_QUI

# Modalità: 'direct' o 'backbone'
mode = direct

# Numero di proxy per pagina (max 100)
page_size = 100

# Ritardo tra richieste API (secondi)
delay_between_requests = 0.4

# ID del piano (opzionale)
plan_id = 

[general]
# File di output per i proxy Webshare
webshare_out = proxy_list.txt

# Cancella il file alla chiusura del programma
cleanup_on_exit = true
```

### 2️⃣ Verifica Configurazione

```bash
# Test fetch proxy
python3 webshare_fetcher.py

# Dovresti vedere:
# ✓ Salvati 500 proxy in proxy_list.txt
```

---

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

### 🔄 Proxy non cambiano

**Problema**: Rotazione non funziona

**Soluzione**:
```bash
# Verifica che il rotator sia attivo
ps aux | grep proxy_rotator

# Controlla log per errori
# Riavvia il C2
```

### 🌐 Errore: "HTTP 400" da Webshare

**Problema**: Configurazione Webshare errata

**Soluzione**:
- Verifica `mode` in config.ini (deve essere `direct` o `backbone`)
- Verifica `plan_id` se necessario
- Controlla validità token

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

### Q: Posso usare più istanze del proxy rotator?
**A**: Sì, usa porte diverse: `python3 proxy_c2.py --port 8889`

### Q: Come verifico che il proxy funzioni?
**A**: 
```bash
# Test HTTP
curl -x http://127.0.0.1:8888 http://httpbin.org/ip

# Test HTTPS
curl -x http://127.0.0.1:8888 https://httpbin.org/ip
```

### Q: I proxy Webshare hanno limiti di banda?
**A**: Dipende dal tuo piano Webshare. Controlla su https://proxy.webshare.io

---

## 📝 File del Progetto

```
project1/
├── proxy_c2.py              # C2 orchestratore (AVVIA QUESTO)
├── proxy_rotator.py         # Server proxy con rotazione
├── webshare_fetcher.py      # Fetcher proxy Webshare
├── config.ini               # Configurazione Webshare
├── proxy_list.txt           # Lista proxy (auto-generato)
└── README_PROXY.md          # Questa documentazione
```

---

## 🎯 Quick Start

```bash
# 1. Installa dipendenze
pip3 install requests

# 2. Configura token in config.ini
nano config.ini  # Inserisci il tuo token Webshare

# 3. Avvia il sistema
python3 proxy_c2.py

# 4. Configura ZAP/Burp
# Proxy: 127.0.0.1:8888

# 5. Profit! 🎉
```

---

## 📞 Supporto

Per problemi o domande:
1. Controlla la sezione [Troubleshooting](#-troubleshooting)
2. Verifica i log del C2
3. Controlla i log del proxy rotator

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
```
