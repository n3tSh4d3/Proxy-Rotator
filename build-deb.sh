#!/bin/bash
#
# build-deb.sh - Build script for proxy-rotator Debian package
#
# Copyright © 2025 CONDRò Adriano
#

set -e

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  Proxy Rotator - Build Pacchetto DEB${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""

# Variabili
PACKAGE_NAME="proxy-rotator"
VERSION="1.0.1"
ARCH="all"
DEB_FILE="${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
BUILD_DIR="debian"
DIST_DIR="dist"

# Verifica che siamo nella directory corretta
if [ ! -f "proxy_c2.py" ] || [ ! -f "proxy_rotator.py" ]; then
    echo -e "${RED}❌ Errore: esegui questo script dalla directory del progetto${NC}"
    exit 1
fi

# Crea directory dist se non esiste
mkdir -p "$DIST_DIR"

echo -e "${YELLOW}📋 Copia file Python...${NC}"

# Copia file Python nella struttura debian
cp -v proxy_c2.py "$BUILD_DIR/usr/share/proxy-rotator/"
cp -v proxy_rotator.py "$BUILD_DIR/usr/share/proxy-rotator/"
cp -v webshare_fetcher.py "$BUILD_DIR/usr/share/proxy-rotator/"

echo -e "${GREEN}✓ File Python copiati${NC}"
echo ""

echo -e "${YELLOW}🔧 Imposta permessi...${NC}"

# Imposta permessi corretti
chmod 755 "$BUILD_DIR/DEBIAN/postinst"
chmod 755 "$BUILD_DIR/DEBIAN/prerm"
chmod 755 "$BUILD_DIR/DEBIAN/postrm"
chmod 644 "$BUILD_DIR/DEBIAN/control"

chmod 755 "$BUILD_DIR/usr/local/bin/proxy-c2"
chmod 755 "$BUILD_DIR/usr/local/bin/proxy-rotator"
chmod 755 "$BUILD_DIR/usr/local/bin/webshare-fetcher"

chmod 644 "$BUILD_DIR/usr/share/proxy-rotator/"*.py
chmod 644 "$BUILD_DIR/etc/proxy-rotator/config.ini.example"
chmod 644 "$BUILD_DIR/etc/systemd/system/proxy-c2.service"

echo -e "${GREEN}✓ Permessi impostati${NC}"
echo ""

echo -e "${YELLOW}📦 Build pacchetto DEB...${NC}"

# Build del pacchetto
dpkg-deb --build "$BUILD_DIR" "$DIST_DIR/$DEB_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}✅ Pacchetto creato con successo!${NC}"
    echo -e "${GREEN}============================================================${NC}"
    echo ""
    echo -e "📦 File: ${YELLOW}$DIST_DIR/$DEB_FILE${NC}"
    echo ""
    
    # Mostra informazioni pacchetto
    echo -e "${YELLOW}📋 Informazioni pacchetto:${NC}"
    dpkg-deb --info "$DIST_DIR/$DEB_FILE"
    echo ""
    
    # Mostra contenuto pacchetto
    echo -e "${YELLOW}📂 Contenuto pacchetto:${NC}"
    dpkg-deb --contents "$DIST_DIR/$DEB_FILE"
    echo ""
    
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}  Installazione${NC}"
    echo -e "${GREEN}============================================================${NC}"
    echo ""
    echo "Per installare il pacchetto:"
    echo -e "  ${YELLOW}sudo dpkg -i $DIST_DIR/$DEB_FILE${NC}"
    echo -e "  ${YELLOW}sudo apt install -f${NC}"
    echo ""
    echo "Per disinstallare:"
    echo -e "  ${YELLOW}sudo apt remove $PACKAGE_NAME${NC}"
    echo ""
    echo -e "${GREEN}============================================================${NC}"
else
    echo -e "${RED}❌ Errore durante la creazione del pacchetto${NC}"
    exit 1
fi
