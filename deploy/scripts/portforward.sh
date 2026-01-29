#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

NAMESPACE="demo"
PID_FILE="/tmp/knowledgeweaver-portforward.pid"

# Show usage
usage() {
  cat << USAGE
Usage: $0 {start|stop|status|restart}

Commands:
  start    - Start all port-forwards in background
  stop     - Stop all port-forwards
  status   - Show port-forward status
  restart  - Restart all port-forwards

Services:
  API:       http://localhost:9621
  Langfuse:  http://localhost:3000
  Neo4j:     http://localhost:7474 (browser)
  Neo4j:     bolt://localhost:7687 (bolt)
  Phoenix:   http://localhost:6006

Examples:
  $0 start
  $0 stop
  $0 status
  $0 restart

USAGE
  exit 1
}

# Start port-forward
start_portforward() {
  local service=$1
  local local_port=$2
  local remote_port=$3
  local name=$4
  
  echo -e "${YELLOW}Starting $name...${NC}"
  kubectl port-forward -n "$NAMESPACE" "$service" "$local_port:$remote_port" &>/dev/null &
  local pid=$!
  echo "$pid" >> "$PID_FILE"
  echo -e "${GREEN}✅ $name: localhost:$local_port (PID: $pid)${NC}"
  sleep 1
}

# Start all port-forwards
cmd_start() {
  echo -e "${YELLOW}========================================${NC}"
  echo -e "${YELLOW}  Starting Port Forwards${NC}"
  echo -e "${YELLOW}========================================${NC}"
  echo ""
  
  # Check kubectl
  if ! kubectl cluster-info &>/dev/null; then
    echo -e "${RED}❌ Error: kubectl not configured${NC}"
    echo "Run: aws eks update-kubeconfig --region ap-southeast-2 --name knowledgeweaver-production"
    exit 1
  fi
  
  # Clean up old PID file
  rm -f "$PID_FILE"
  
  # Start all services
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
  
  # Test API
  echo -e "${YELLOW}Testing API health...${NC}"
  sleep 2
  if curl -s http://localhost:9621/health &>/dev/null; then
    echo -e "${GREEN}✅ API is responding${NC}"
  else
    echo -e "${YELLOW}⏳ API may still be starting up${NC}"
  fi
  echo ""
  
  # Open browsers (macOS only)
  if command -v open &> /dev/null; then
    echo -e "${YELLOW}Opening browsers...${NC}"
    sleep 1
    open http://localhost:9621 &
    open http://localhost:3000 &
    open http://localhost:7474 &
    open http://localhost:6006 &
    echo -e "${GREEN}✅ Browsers opened${NC}"
  fi
  echo ""
  
  echo "To stop: $0 stop"
  echo "To check status: $0 status"
}

# Stop all port-forwards
cmd_stop() {
  echo -e "${YELLOW}========================================${NC}"
  echo -e "${YELLOW}  Stopping Port Forwards${NC}"
  echo -e "${YELLOW}========================================${NC}"
  echo ""
  
  if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}⚠️  No PID file found${NC}"
    echo "Attempting to kill all kubectl port-forward processes..."
    
    if pgrep -f "kubectl port-forward" &>/dev/null; then
      pkill -f "kubectl port-forward"
      echo -e "${GREEN}✅ Killed all kubectl port-forward processes${NC}"
    else
      echo -e "${YELLOW}No kubectl port-forward processes found${NC}"
    fi
  else
    echo "Reading PIDs from $PID_FILE..."
    while read -r pid; do
      if [ -n "$pid" ]; then
        if kill -0 "$pid" 2>/dev/null; then
          kill "$pid" 2>/dev/null && echo -e "${GREEN}✅ Stopped PID $pid${NC}"
        else
          echo -e "${YELLOW}⚠️  PID $pid already stopped${NC}"
        fi
      fi
    done < "$PID_FILE"
    
    rm -f "$PID_FILE"
    echo -e "${GREEN}Cleaned up PID file${NC}"
  fi
  
  echo ""
  echo -e "${GREEN}========================================${NC}"
  echo -e "${GREEN}  All Port Forwards Stopped!${NC}"
  echo -e "${GREEN}========================================${NC}"
}

# Show status
cmd_status() {
  echo -e "${YELLOW}========================================${NC}"
  echo -e "${YELLOW}  Port Forward Status${NC}"
  echo -e "${YELLOW}========================================${NC}"
  echo ""
  
  # Check PID file
  if [ -f "$PID_FILE" ]; then
    echo "PID file: $PID_FILE"
    echo ""
    echo "Active port-forwards:"
    
    active=0
    while read -r pid; do
      if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        process_info=$(ps -p "$pid" -o command= 2>/dev/null | sed 's/kubectl port-forward//')
        echo -e "${GREEN}✅ PID $pid:$process_info${NC}"
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
    ps aux | grep "kubectl port-forward" | grep -v grep | awk '{print $2, $11, $12, $13, $14, $15}'
  else
    echo -e "${YELLOW}None running${NC}"
  fi
  
  echo ""
  echo "Service connectivity:"
  
  test_connection() {
    local name=$1
    local url=$2
    echo -n "  $name: "
    if curl -s "$url" &>/dev/null; then
      echo -e "${GREEN}✅ Reachable${NC}"
    else
      echo -e "${RED}❌ Not reachable${NC}"
    fi
  }
  
  test_connection "API (9621)      " "http://localhost:9621/health"
  test_connection "Langfuse (3000) " "http://localhost:3000"
  test_connection "Neo4j (7474)    " "http://localhost:7474"
  test_connection "Phoenix (6006)  " "http://localhost:6006"
  
  echo ""
}

# Restart
cmd_restart() {
  echo -e "${YELLOW}Restarting port-forwards...${NC}"
  echo ""
  cmd_stop
  echo ""
  sleep 2
  cmd_start
}

# Main
case "${1:-}" in
  start)
    cmd_start
    ;;
  stop)
    cmd_stop
    ;;
  status)
    cmd_status
    ;;
  restart)
    cmd_restart
    ;;
  *)
    usage
    ;;
esac
