#!/bin/bash

# OpenPoke iMessage Bot Startup Script
# This script starts both the Python backend and Node.js iMessage service

set -e

echo "================================================="
echo "  Starting OpenPoke with iMessage Integration"
echo "================================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo -e "${RED}Error: iMessage integration only works on macOS${NC}"
    exit 1
fi

# Check if Python backend directory exists
if [ ! -d "server" ]; then
    echo -e "${RED}Error: server directory not found${NC}"
    exit 1
fi

# Check if iMessage service directory exists
if [ ! -d "imessage-service" ]; then
    echo -e "${RED}Error: imessage-service directory not found${NC}"
    exit 1
fi

# Check if .env exists in imessage-service
if [ ! -f "imessage-service/.env" ]; then
    echo -e "${YELLOW}Warning: imessage-service/.env not found, copying from .env.example${NC}"
    if [ -f "imessage-service/.env.example" ]; then
        cp imessage-service/.env.example imessage-service/.env
        echo -e "${GREEN}Created imessage-service/.env${NC}"
    else
        echo -e "${RED}Error: imessage-service/.env.example not found${NC}"
        exit 1
    fi
fi

# Check if node_modules exists
if [ ! -d "imessage-service/node_modules" ]; then
    echo -e "${YELLOW}Installing Node.js dependencies...${NC}"
    cd imessage-service && npm install && cd ..
    echo -e "${GREEN}✓ Dependencies installed${NC}"
fi

# Check if TypeScript is compiled
if [ ! -d "imessage-service/dist" ]; then
    echo -e "${YELLOW}Building TypeScript code...${NC}"
    cd imessage-service && npm run build && cd ..
    echo -e "${GREEN}✓ Build complete${NC}"
fi

echo ""
echo -e "${GREEN}Starting services...${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}✓ Backend stopped${NC}"
    fi
    if [ ! -z "$IMESSAGE_PID" ]; then
        kill $IMESSAGE_PID 2>/dev/null || true
        echo -e "${GREEN}✓ iMessage service stopped${NC}"
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start Python backend
echo -e "${GREEN}[1/2] Starting Python backend...${NC}"

# Check if venv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}Error: Virtual environment not activated${NC}"
    echo -e "${YELLOW}Please activate it first: source .venv/bin/activate${NC}"
    exit 1
fi

# Run from project root, not from server directory
python -m uvicorn server.app:app --host 0.0.0.0 --port 8001 &
BACKEND_PID=$!
sleep 2

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}Error: Backend failed to start${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Backend running on http://localhost:8001 (PID: $BACKEND_PID)${NC}"
echo ""

# Start iMessage service
echo -e "${GREEN}[2/2] Starting iMessage service...${NC}"
cd imessage-service
npm start &
IMESSAGE_PID=$!
cd ..
sleep 2

# Check if iMessage service is running
if ! kill -0 $IMESSAGE_PID 2>/dev/null; then
    echo -e "${RED}Error: iMessage service failed to start${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi
echo -e "${GREEN}✓ iMessage service running (PID: $IMESSAGE_PID)${NC}"
echo ""

echo "================================================="
echo -e "${GREEN}  All services running!${NC}"
echo "================================================="
echo ""
echo "Backend API:     http://localhost:8001"
echo "API Docs:        http://localhost:8001/docs"
echo "iMessage Bot:    Watching for messages..."
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for both processes
wait

