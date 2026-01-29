#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PID_FILE="/tmp/knowledgeweaver-portforward.pid"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  Stopping Port Forwards${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
  echo -e "${YELLOW}⚠️  No PID file found at $PID_FILE${NC}"
  echo "Attempting to find and kill all kubectl port-forward processes..."
  
  # Kill all kubectl port-forward processes
  if pgrep -f "kubectl port-forward" &>/dev/null; then
    pkill -f "kubectl port-forward"
    echo -e "${GREEN}✅ Killed all kubectl port-forward processes${NC}"
  else
    echo -e "${YELLOW}No kubectl port-forward processes found${NC}"
  fi
  exit 0
fi

# Read PIDs and kill them
echo "Reading PIDs from $PID_FILE..."
while read -r pid; do
  if [ -n "$pid" ]; then
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null && echo -e "${GREEN}✅ Stopped process $pid${NC}" || echo -e "${YELLOW}⚠️  Failed to stop $pid${NC}"
    else
      echo -e "${YELLOW}⚠️  Process $pid already stopped${NC}"
    fi
  fi
done < "$PID_FILE"

# Clean up PID file
rm -f "$PID_FILE"
echo -e "${GREEN}Cleaned up PID file${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  All Port Forwards Stopped!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
