#!/bin/bash

# OpenPoke iMessage Bot Setup Script
# Run this ONCE to set up everything needed for iMessage integration

set -e

echo "================================================="
echo "  OpenPoke iMessage Bot - Setup"
echo "================================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo -e "${RED}Error: iMessage integration only works on macOS${NC}"
    exit 1
fi

echo -e "${GREEN}[1/4] Checking Python virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating one...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi

echo ""
echo -e "${GREEN}[2/4] Installing Node.js dependencies...${NC}"
cd imessage-service

if [ ! -f "package.json" ]; then
    echo -e "${RED}Error: package.json not found in imessage-service/${NC}"
    exit 1
fi

npm install
echo -e "${GREEN}✓ Node.js dependencies installed${NC}"

echo ""
echo -e "${GREEN}[3/4] Building TypeScript code...${NC}"
npm run build
echo -e "${GREEN}✓ TypeScript compiled${NC}"

cd ..

echo ""
echo -e "${GREEN}[4/4] Setting up configuration...${NC}"

# Check if .env exists
if [ ! -f "imessage-service/.env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cat > imessage-service/.env << 'EOF'
# Backend API Configuration
BACKEND_URL=http://localhost:8001

# iMessage Watcher Configuration
POLL_INTERVAL=2000

# Debug Mode
DEBUG=true

# Allowed Phone Numbers (comma-separated)
# ⚠️ IMPORTANT: Replace with YOUR phone number(s)!
# Leave empty to respond to ALL (not recommended)
# Example: ALLOWED_NUMBERS=+11234567890,+10987654321
ALLOWED_NUMBERS=
EOF
    echo -e "${GREEN}✓ Created imessage-service/.env${NC}"
    echo ""
    echo -e "${YELLOW}=================================================${NC}"
    echo -e "${YELLOW}  ⚠️  IMPORTANT: Configure Your Phone Number!${NC}"
    echo -e "${YELLOW}=================================================${NC}"
    echo ""
    echo -e "Edit ${YELLOW}imessage-service/.env${NC} and set ALLOWED_NUMBERS"
    echo -e "to your phone number (e.g., ${GREEN}ALLOWED_NUMBERS=+11234567890${NC})"
    echo ""
    echo -e "Without this, the bot will respond to ${RED}EVERYONE${NC} who texts you!"
    echo ""
    echo -e "To edit now: ${GREEN}nano imessage-service/.env${NC}"
    echo ""
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
    
    # Check if ALLOWED_NUMBERS is set
    if grep -q "^ALLOWED_NUMBERS=$" imessage-service/.env || ! grep -q "^ALLOWED_NUMBERS=" imessage-service/.env; then
        echo ""
        echo -e "${YELLOW}⚠️  WARNING: ALLOWED_NUMBERS not configured!${NC}"
        echo -e "Edit ${YELLOW}imessage-service/.env${NC} and add your phone number"
        echo ""
    fi
fi

echo ""
echo "================================================="
echo -e "${GREEN}  Setup Complete!${NC}"
echo "================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. ${YELLOW}Configure phone number:${NC}"
echo "   nano imessage-service/.env"
echo "   (Set ALLOWED_NUMBERS to your phone number)"
echo ""
echo "2. ${YELLOW}Grant Full Disk Access:${NC}"
echo "   System Settings → Privacy & Security → Full Disk Access"
echo "   Add your Terminal or IDE, then restart it"
echo ""
echo "3. ${YELLOW}Start the bot:${NC}"
echo "   ./start-imessage.sh"
echo ""
echo "4. ${YELLOW}Test:${NC}"
echo "   Send yourself a text from another device!"
echo ""

