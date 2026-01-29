#!/bin/bash
# Check KnowledgeWeaver Service Status
# 检查 KnowledgeWeaver 服务状态

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

PID_FILE="$PROJECT_ROOT/logs/server.pid"

echo ""
echo "======================================================================"
echo -e "${BLUE}📊 KnowledgeWeaver 服务状态${NC}"
echo "======================================================================"
echo ""

# 检查配置
if [ -f "$PROJECT_ROOT/.env" ]; then
    PORT=$(grep "^PORT=" "$PROJECT_ROOT/.env" | cut -d '=' -f2 | tr -d ' ')
    PORT=${PORT:-9621}
    HOST=$(grep "^HOST=" "$PROJECT_ROOT/.env" | cut -d '=' -f2 | tr -d ' ')
    HOST=${HOST:-0.0.0.0}
    USE_NEO4J=$(grep "^USE_NEO4J=" "$PROJECT_ROOT/.env" | cut -d '=' -f2 | tr -d ' ')
else
    PORT=9621
    HOST="0.0.0.0"
    USE_NEO4J="false"
fi

# 检查服务状态
SERVICE_RUNNING=false

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        print_success "后端服务运行中 (PID: $PID)"
        SERVICE_RUNNING=true
    else
        print_error "PID 文件存在但进程未运行"
    fi
else
    # 通过端口检查
    if command -v lsof &> /dev/null; then
        PID=$(lsof -ti:$PORT 2>/dev/null)
        if [ -n "$PID" ]; then
            print_success "后端服务运行中 (PID: $PID, 端口: $PORT)"
            SERVICE_RUNNING=true
        else
            print_error "后端服务未运行"
        fi
    else
        print_error "无法检测服务状态（lsof 命令不可用）"
    fi
fi

echo ""

# 如果服务运行中，显示访问信息
if [ "$SERVICE_RUNNING" = true ]; then
    echo "访问地址:"
    echo "  • 前端界面: http://localhost:$PORT"
    echo "  • API 文档:  http://localhost:$PORT/docs"
    echo "  • 健康检查: http://localhost:$PORT/health"
    echo ""

    # 尝试健康检查
    if command -v curl &> /dev/null; then
        print_info "正在进行健康检查..."
        HEALTH_RESPONSE=$(curl -s http://localhost:$PORT/health 2>/dev/null)
        if [ $? -eq 0 ]; then
            print_success "健康检查通过"
            echo "  响应: $HEALTH_RESPONSE"
        else
            print_error "健康检查失败"
        fi
        echo ""
    fi
fi

# 检查 Neo4j 状态
if [ "$USE_NEO4J" = "true" ]; then
    NEO4J_URI=$(grep "^NEO4J_URI=" "$PROJECT_ROOT/.env" | cut -d '=' -f2 | tr -d ' ')
    NEO4J_HOST=$(echo "$NEO4J_URI" | sed 's|bolt://||' | cut -d ':' -f1)
    NEO4J_PORT=$(echo "$NEO4J_URI" | sed 's|bolt://||' | cut -d ':' -f2)

    if command -v nc &> /dev/null; then
        if nc -z "$NEO4J_HOST" "$NEO4J_PORT" 2>/dev/null; then
            print_success "Neo4j 运行中 ($NEO4J_URI)"
        else
            print_error "Neo4j 未运行 ($NEO4J_URI)"
        fi
    else
        print_info "Neo4j 配置: $NEO4J_URI"
    fi
else
    print_info "使用本地文件存储（Neo4j 已禁用）"
fi

echo ""
