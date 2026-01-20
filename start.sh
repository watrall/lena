#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting LENA Pilot...${NC}"

# 1. Check Prerequisites
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed or not in PATH.${NC}"
    exit 1
fi

echo "Checking ports..."
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}Warning: Port 3000 is in use. Trying to clear...${NC}"
    kill -9 $(lsof -t -i:3000) || true
fi
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}Warning: Port 8000 is in use. Trying to clear...${NC}"
    kill -9 $(lsof -t -i:8000) || true
fi

# 2. Environment Setup
if [ ! -f .env ]; then
    echo "Creating .env from example..."
    cp .env.example .env
    # Ensure offline mode for consistency in demos
    sed -i '' 's/# LENA_LLM_MODE=hf/LENA_LLM_MODE=off/' .env
fi

# 3. Launch Docker
echo -e "${GREEN}Building and starting containers...${NC}"
docker compose -f docker/docker-compose.yml up --build -d

# 4. Wait for Backend
echo "Waiting for Backend API to be ready..."
MAX_RETRIES=30
COUNT=0
URL="http://localhost:8000/healthz"

while ! curl -s $URL > /dev/null; do
    sleep 2
    COUNT=$((COUNT+1))
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo -e "${RED}Backend failed to start in time. Check logs with: docker logs docker-api-1${NC}"
        exit 1
    fi
    echo -n "."
done
echo -e "\n${GREEN}Backend is up!${NC}"

# 5. Seed Data
echo "Seeding pilot data..."
if curl -s -X POST http://localhost:8000/ingest/run > /dev/null; then
    echo -e "${GREEN}Data seeded.${NC}"
else
    echo -e "${YELLOW}Skipped seeding (ingest endpoint disabled or unavailable).${NC}"
fi

# 6. Launch Browser
echo -e "${GREEN}LENA is ready! Opening browser...${NC}"
case "$(uname)" in
   "Darwin") open http://localhost:3000 ;;
   "Linux")  xdg-open http://localhost:3000 ;;
   *)        echo "Open http://localhost:3000 in your browser" ;;
esac
