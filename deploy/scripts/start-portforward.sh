#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

NAMESPACE="demo"
PID_FILE="/tmp/knowledgeweaver-portforward.pid"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  Starting Port Forwards${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Clean up old PID file
rm -f "$PID_FILE"

# Check if kubectl is configured
if ! kubectl cluster-info &>/dev/null; then
  echo -e "${RED}❌ Error: kubectl not configured${NC}"
  echo "Run: aws eks update-kubeconfig --region ap-southeast-2 --name knowledgeweaver-production"
  exit 1
fi

# Function to start port-forward
start_portforward() {
  local service=$1
  local local_port=$2
  local remote_port=$3
  local name=$4
  
  echo -e "${YELLOW}Starting port-forward for $name...${NC}"
  kubectl port-forward -n "$NAMESPACE" "$service" "$local_port:$remote_port" &>/dev/null &
  local pid=$!
  echo "$pid" >> "$PID_FILE"
  echo -e "${GREEN}✅ $name: localhost:$local_port (PID: $pid)${NC}"
  sleep 1
}

# Start all port-forwards
start_portforward "svc/api" 9621 9621 "API"
start_portforward "svc/langfuse" 3000 3000 "Langfuse"
start_portforward "neo4j-0" 7474 7474 "Neo4j Browser"
start_portforward "neo4j-0" 7687 7687 "Neo4j Bolt"
start_portforward "svc/phoenix" 6006 6006 "Phoenix"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  All Port Forwards Started!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

echo "Services available at:"
echo "  • API:            http://localhost:9621"
echo "  • Langfuse:       http://localhost:3000"
echo "  • Neo4j Browser:  http://localhost:7474"
echo "  • Neo4j Bolt:     bolt://localhost:7687"
echo "  • Phoenix:        http://localhost:6006"
echo ""

# Test API health
echo -e "${YELLOW}Testing API health...${NC}"
sleep 2
if curl -s http://localhost:9621/health &>/dev/null; then
  echo -e "${GREEN}✅ API is responding${NC}"
else
  echo -e "${YELLOW}⏳ API may still be starting up${NC}"
fi
echo ""

# Open browsers (optional, comment out if not desired)
echo -e "${YELLOW}Opening browsers...${NC}"
if command -v open &> /dev/null; then
  sleep 1
  open http://localhost:9621 &
  open http://localhost:3000 &
  open http://localhost:7474 &
  open http://localhost:6006 &
  echo -e "${GREEN}✅ Browsers opened${NC}"
else
  echo -e "${YELLOW}⚠️  'open' command not found (macOS only)${NC}"
  echo "Manually open the URLs above"
fi
echo ""

echo "PIDs saved to: $PID_FILE"
echo "To stop all port-forwards, run:"
echo "  bash deploy/scripts/stop-portforward.sh"
echo ""
