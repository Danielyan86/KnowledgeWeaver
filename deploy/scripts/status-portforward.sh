#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PID_FILE="/tmp/knowledgeweaver-portforward.pid"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  Port Forward Status${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Check if PID file exists
if [ -f "$PID_FILE" ]; then
  echo "PID file found at: $PID_FILE"
  echo ""
  echo "Active port-forwards:"
  
  active=0
  while read -r pid; do
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      # Get process info
      process_info=$(ps -p "$pid" -o command= 2>/dev/null)
      echo -e "${GREEN}✅ PID $pid: $process_info${NC}"
      ((active++))
    fi
  done < "$PID_FILE"
  
  echo ""
  echo "Active processes: $active"
else
  echo -e "${YELLOW}No PID file found${NC}"
fi

echo ""
echo "All kubectl port-forward processes:"
if pgrep -f "kubectl port-forward" &>/dev/null; then
  ps aux | grep "kubectl port-forward" | grep -v grep
else
  echo -e "${YELLOW}No kubectl port-forward processes running${NC}"
fi

echo ""
echo "Test connections:"
echo -n "  API (9621):       "
if curl -s http://localhost:9621/health &>/dev/null; then
  echo -e "${GREEN}✅ Reachable${NC}"
else
  echo -e "${RED}❌ Not reachable${NC}"
fi

echo -n "  Langfuse (3000):  "
if curl -s http://localhost:3000 &>/dev/null; then
  echo -e "${GREEN}✅ Reachable${NC}"
else
  echo -e "${RED}❌ Not reachable${NC}"
fi

echo -n "  Neo4j (7474):     "
if curl -s http://localhost:7474 &>/dev/null; then
  echo -e "${GREEN}✅ Reachable${NC}"
else
  echo -e "${RED}❌ Not reachable${NC}"
fi

echo -n "  Phoenix (6006):   "
if curl -s http://localhost:6006 &>/dev/null; then
  echo -e "${GREEN}✅ Reachable${NC}"
else
  echo -e "${RED}❌ Not reachable${NC}"
fi

echo ""
