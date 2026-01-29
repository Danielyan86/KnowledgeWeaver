#!/bin/bash
# KnowledgeWeaver Startup Script
# 启动 KnowledgeWeaver 服务

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_header() {
    echo ""
    echo "======================================================================"
    echo -e "${BLUE}$1${NC}"
    echo "======================================================================"
}

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 切换到项目根目录
cd "$PROJECT_ROOT"

print_header "🚀 KnowledgeWeaver 启动脚本"

# 步骤 1: 检查 Python 环境
print_info "步骤 1/4: 检查 Python 环境..."
if ! command -v python &> /dev/null; then
    print_error "Python 未安装！请先安装 Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
print_success "Python 版本: $PYTHON_VERSION"

# 步骤 2: 检查环境变量
print_info "步骤 2/4: 检查环境配置..."
if [ ! -f ".env" ]; then
    print_warning ".env 文件不存在！"
    print_info "正在从 .env.example 复制..."
    cp .env.example .env
    print_warning "请编辑 .env 文件配置必要的 API 密钥和数据库连接！"
    print_info "配置完成后，重新运行此脚本。"
    exit 1
fi
print_success ".env 配置文件存在"

# 步骤 3: 检查依赖
print_info "步骤 3/4: 检查 Python 依赖..."
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    print_warning "未检测到虚拟环境，建议创建虚拟环境："
    print_info "  python -m venv venv"
    print_info "  source venv/bin/activate  # Linux/Mac"
    print_info "  pip install -r requirements.txt"
    echo ""
fi

# 检查关键依赖
if ! python -c "import fastapi" 2>/dev/null; then
    print_error "FastAPI 未安装！请运行: pip install -r requirements.txt"
    exit 1
fi
print_success "Python 依赖已安装"

# 步骤 4: 检查 Neo4j（可选）
print_info "步骤 4/4: 检查 Neo4j 状态..."
USE_NEO4J=$(grep "^USE_NEO4J=" .env | cut -d '=' -f2 | tr -d ' ')

if [ "$USE_NEO4J" = "true" ]; then
    NEO4J_URI=$(grep "^NEO4J_URI=" .env | cut -d '=' -f2 | tr -d ' ')
    NEO4J_HOST=$(echo "$NEO4J_URI" | sed 's|bolt://||' | cut -d ':' -f1)
    NEO4J_PORT=$(echo "$NEO4J_URI" | sed 's|bolt://||' | cut -d ':' -f2)

    if command -v nc &> /dev/null; then
        if nc -z "$NEO4J_HOST" "$NEO4J_PORT" 2>/dev/null; then
            print_success "Neo4j 运行中 ($NEO4J_URI)"
        else
            print_warning "Neo4j 未运行 ($NEO4J_URI)"
            print_info "请启动 Neo4j，或设置 USE_NEO4J=false 使用本地文件存储"

            # 询问是否继续
            read -p "是否继续启动服务？(y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_info "已取消启动"
                exit 0
            fi
        fi
    else
        print_warning "无法检测 Neo4j 状态（nc 命令不可用）"
    fi
else
    print_info "使用本地文件存储（Neo4j 已禁用）"
fi

# 步骤 5: 创建必要的目录
print_info "创建数据目录..."
mkdir -p data/inputs/__enqueued__
mkdir -p data/storage/vector_db
mkdir -p data/checkpoints
mkdir -p data/progress
mkdir -p logs
print_success "数据目录已就绪"

# 步骤 6: 读取配置
HOST=$(grep "^HOST=" .env | cut -d '=' -f2 | tr -d ' ')
PORT=$(grep "^PORT=" .env | cut -d '=' -f2 | tr -d ' ')
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-9621}

# 步骤 7: 检查端口占用
print_info "检查端口 $PORT..."
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_error "端口 $PORT 已被占用！"
    print_info "请停止占用该端口的进程，或修改 .env 中的 PORT 配置"
    lsof -Pi :$PORT -sTCP:LISTEN
    exit 1
fi
print_success "端口 $PORT 可用"

# 步骤 8: 启动服务
print_header "🌟 启动服务"

# 创建 PID 文件目录
PID_DIR="$PROJECT_ROOT/logs"
PID_FILE="$PID_DIR/server.pid"

# 启动后端服务（包含前端）
print_info "正在启动 KnowledgeWeaver 服务..."
echo ""

# 保存当前脚本的 PID 以便 Ctrl+C 时清理
trap 'kill $(cat $PID_FILE 2>/dev/null) 2>/dev/null; rm -f $PID_FILE; print_warning "服务已停止"; exit 0' INT TERM

# 启动服务并保存 PID
python -m backend.server &
echo $! > "$PID_FILE"

# 等待服务启动
sleep 2

# 检查服务是否成功启动
if ! kill -0 $(cat "$PID_FILE" 2>/dev/null) 2>/dev/null; then
    print_error "服务启动失败！请检查日志"
    rm -f "$PID_FILE"
    exit 1
fi

print_success "服务启动成功！"

# 显示访问信息
print_header "📍 服务访问信息"
echo ""
echo -e "${GREEN}✓ 前端界面:${NC}  http://localhost:$PORT"
echo -e "${GREEN}✓ API 文档:${NC}   http://localhost:$PORT/docs"
echo -e "${GREEN}✓ 健康检查:${NC}   http://localhost:$PORT/health"
echo ""
print_info "按 Ctrl+C 停止服务"
echo ""

# 持续运行，等待用户中断
wait
