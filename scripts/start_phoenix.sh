#!/bin/bash

# Phoenix 快速启动脚本
# 用于快速启动 Phoenix 服务并验证配置

set -e

echo "🚀 启动 Phoenix 服务..."
echo ""

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker"
    exit 1
fi

# 启动 Phoenix
echo "📦 启动 Phoenix 容器..."
docker-compose -f docker-compose.phoenix.yml up -d

# 等待服务启动
echo "⏳ 等待 Phoenix 启动..."
sleep 5

# 检查服务状态
if curl -s http://localhost:6006 > /dev/null; then
    echo ""
    echo "✅ Phoenix 已成功启动！"
    echo ""
    echo "📊 访问地址："
    echo "   Phoenix UI:  http://localhost:6006"
    echo "   OTEL gRPC:   localhost:4317"
    echo "   OTEL HTTP:   http://localhost:4318"
    echo ""
    echo "🔧 下一步："
    echo "   1. 在 .env 文件中设置 PHOENIX_ENABLED=true"
    echo "   2. 重启应用服务"
    echo "   3. 执行一些 LLM 调用"
    echo "   4. 在 Phoenix UI 查看追踪数据"
    echo ""
else
    echo ""
    echo "⚠️ Phoenix 启动可能失败，请检查日志："
    echo "   docker logs phoenix"
    echo ""
fi
