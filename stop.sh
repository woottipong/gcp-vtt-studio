#!/bin/bash

# Auto VTT Studio - Stop Script
# This script stops both backend and frontend services

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   Auto VTT Studio - Stopping Services${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Function to kill process by PID
kill_process() {
    local pid=$1
    local name=$2
    
    if [ ! -z "$pid" ]; then
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${YELLOW}Stopping $name (PID: $pid)${NC}"
            kill -15 $pid 2>/dev/null || kill -9 $pid 2>/dev/null || true
            sleep 1
            
            # Check if process is still running
            if ps -p $pid > /dev/null 2>&1; then
                kill -9 $pid 2>/dev/null || true
                sleep 1
            fi
            
            echo -e "${GREEN}✓ $name stopped${NC}"
        else
            echo -e "${YELLOW}$name (PID: $pid) is not running${NC}"
        fi
    fi
}

# Stop Backend
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    kill_process $BACKEND_PID "Backend"
    rm -f .backend.pid
else
    echo -e "${YELLOW}Backend PID file not found${NC}"
fi

# Stop Frontend
if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    kill_process $FRONTEND_PID "Frontend"
    rm -f .frontend.pid
else
    echo -e "${YELLOW}Frontend PID file not found${NC}"
fi

# Kill any remaining processes on ports 8000 and 5173
echo ""
echo -e "${YELLOW}Checking for remaining processes on ports...${NC}"

BACKEND_PORT_PID=$(lsof -ti:8000 2>/dev/null || true)
if [ ! -z "$BACKEND_PORT_PID" ]; then
    echo -e "${YELLOW}Found process on port 8000 (PID: $BACKEND_PORT_PID), killing...${NC}"
    kill -9 $BACKEND_PORT_PID 2>/dev/null || true
fi

FRONTEND_PORT_PID=$(lsof -ti:5173 2>/dev/null || true)
if [ ! -z "$FRONTEND_PORT_PID" ]; then
    echo -e "${YELLOW}Found process on port 5173 (PID: $FRONTEND_PORT_PID), killing...${NC}"
    kill -9 $FRONTEND_PORT_PID 2>/dev/null || true
fi

# Clean logs
echo ""
echo -e "${YELLOW}Cleaning logs...${NC}"
if [ -d "logs" ]; then
    rm -rf logs/*
    echo -e "${GREEN}✓ Logs cleaned${NC}"
else
    echo -e "${YELLOW}logs/ directory not found${NC}"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ All services stopped & logs cleaned${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
