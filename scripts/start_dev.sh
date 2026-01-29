#!/bin/bash
# Quick Start Script for Development
# 开发环境快速启动脚本（跳过所有检查）

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# 读取配置
if [ -f ".env" ]; then
    PORT=$(grep "^PORT=" .env | cut -d '=' -f2 | tr -d ' ')
    PORT=${PORT:-9621}
else
    PORT=9621
fi

echo ""
echo "======================================================================"
echo -e "${BLUE}🚀 KnowledgeWeaver 快速启动 (开发模式)${NC}"
echo "======================================================================"
echo ""
echo -e "${GREEN}✓ 前端界面:${NC}  http://localhost:$PORT"
echo -e "${GREEN}✓ API 文档:${NC}   http://localhost:$PORT/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 启动服务
python -m backend.server
