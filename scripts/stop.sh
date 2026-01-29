#!/bin/bash
# Stop KnowledgeWeaver Service
# 停止 KnowledgeWeaver 服务

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

PID_FILE="$PROJECT_ROOT/logs/server.pid"

echo ""
echo "停止 KnowledgeWeaver 服务..."
echo ""

# 方法 1: 通过 PID 文件停止
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        rm -f "$PID_FILE"
        print_success "服务已停止 (PID: $PID)"
        exit 0
    else
        print_warning "PID 文件存在但进程未运行"
        rm -f "$PID_FILE"
    fi
fi

# 方法 2: 通过端口查找并停止
if [ -f "$PROJECT_ROOT/.env" ]; then
    PORT=$(grep "^PORT=" "$PROJECT_ROOT/.env" | cut -d '=' -f2 | tr -d ' ')
    PORT=${PORT:-9621}

    PID=$(lsof -ti:$PORT)
    if [ -n "$PID" ]; then
        kill "$PID"
        print_success "服务已停止 (端口: $PORT, PID: $PID)"
        exit 0
    fi
fi

# 方法 3: 通过进程名查找
PID=$(pgrep -f "python.*backend\.server" | head -1)
if [ -n "$PID" ]; then
    kill "$PID"
    print_success "服务已停止 (PID: $PID)"
    exit 0
fi

print_warning "未找到运行中的服务"
