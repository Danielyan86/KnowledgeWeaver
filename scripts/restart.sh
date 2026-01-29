#!/bin/bash
# Restart KnowledgeWeaver Service
# 重启 KnowledgeWeaver 服务

# 颜色定义
BLUE='\033[0;34m'
NC='\033[0m'

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo -e "${BLUE}🔄 重启 KnowledgeWeaver 服务${NC}"
echo ""

# 停止服务
bash "$SCRIPT_DIR/stop.sh"

# 等待 2 秒
sleep 2

# 启动服务
bash "$SCRIPT_DIR/start.sh"
