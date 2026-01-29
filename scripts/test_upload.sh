#!/bin/bash
# 测试文档上传和进度追踪

echo "=== 测试 KnowledgeWeaver 完整流程 ==="
echo ""

# 1. 检查 Neo4j 连接
echo "1. 检查 Neo4j 连接..."
python -c "from backend.neo4j_storage import get_neo4j_storage; storage = get_neo4j_storage(); stats = storage.get_stats(); print(f'✓ Neo4j 连接成功: {stats}')"

if [ $? -ne 0 ]; then
    echo "✗ Neo4j 连接失败"
    exit 1
fi

echo ""

# 2. 检查后端服务
echo "2. 检查后端服务..."
curl -s http://localhost:9621/health | jq .
if [ $? -ne 0 ]; then
    echo "✗ 后端服务未运行，请先启动: cd backend && python server.py"
    exit 1
fi

echo ""

# 3. 上传测试文件
echo "3. 上传测试文件..."
TEST_FILE="tests/data/test_small.txt"

if [ ! -f "$TEST_FILE" ]; then
    echo "✗ 测试文件不存在: $TEST_FILE"
    exit 1
fi

UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:9621/documents/upload-async \
    -F "file=@${TEST_FILE}")

echo "$UPLOAD_RESPONSE" | jq .

DOC_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.doc_id')

if [ -z "$DOC_ID" ] || [ "$DOC_ID" = "null" ]; then
    echo "✗ 上传失败"
    exit 1
fi

echo "✓ 文档已上传，doc_id: $DOC_ID"
echo ""

# 4. 轮询进度
echo "4. 监控处理进度..."
while true; do
    PROGRESS=$(curl -s http://localhost:9621/documents/progress/${DOC_ID})

    STATUS=$(echo "$PROGRESS" | jq -r '.status')
    CURRENT=$(echo "$PROGRESS" | jq -r '.current')
    TOTAL=$(echo "$PROGRESS" | jq -r '.total')
    STAGE=$(echo "$PROGRESS" | jq -r '.stage')
    PERCENT=$(echo "$PROGRESS" | jq -r '.progress')

    echo -ne "\r进度: $PERCENT% ($CURRENT/$TOTAL) - $STAGE                    "

    if [ "$STATUS" = "completed" ]; then
        echo ""
        echo "✓ 处理完成！"
        break
    elif [ "$STATUS" = "failed" ]; then
        echo ""
        ERROR=$(echo "$PROGRESS" | jq -r '.error')
        echo "✗ 处理失败: $ERROR"
        exit 1
    fi

    sleep 1
done

echo ""

# 5. 检查 Neo4j 数据
echo "5. 检查 Neo4j 数据..."
curl -s http://localhost:9621/stats | jq .

echo ""

# 6. 查看图谱
echo "6. 查看图谱（前 5 个节点）..."
curl -s http://localhost:9621/graphs | jq '.nodes[:5]'

echo ""
echo "=== 测试完成 ==="
echo "请访问 http://localhost:9621 查看前端界面"
