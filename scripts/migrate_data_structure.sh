#!/bin/bash
# KnowledgeWeaver 数据目录重构脚本
# 方案 A：统一数据目录

set -e  # 遇到错误立即退出

echo "========================================="
echo "KnowledgeWeaver 数据目录重构"
echo "========================================="
echo ""

# 获取脚本所在目录（项目根目录）
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo "项目根目录: $PROJECT_ROOT"
echo ""

# 1. 创建新的目录结构
echo "[1/6] 创建新的目录结构..."
mkdir -p data/storage/graphs
mkdir -p data/storage/rag
mkdir -p data/storage/vector_db
mkdir -p data/cache
mkdir -p logs

echo "  ✓ 创建 data/storage/graphs"
echo "  ✓ 创建 data/storage/rag"
echo "  ✓ 创建 data/storage/vector_db"
echo "  ✓ 创建 data/cache"
echo "  ✓ 创建 logs"
echo ""

# 2. 移动知识图谱数据
echo "[2/6] 移动知识图谱数据..."
if [ -d "data/graphs" ] && [ "$(ls -A data/graphs 2>/dev/null)" ]; then
    mv data/graphs/* data/storage/graphs/ 2>/dev/null || true
    rmdir data/graphs
    echo "  ✓ 移动 data/graphs/* -> data/storage/graphs/"
else
    echo "  ⊘ data/graphs/ 为空或不存在，跳过"
fi
echo ""

# 3. 移动 RAG 存储数据
echo "[3/6] 移动 RAG 存储数据..."
if [ -d "rag_storage" ] && [ "$(ls -A rag_storage 2>/dev/null)" ]; then
    mv rag_storage/* data/storage/rag/ 2>/dev/null || true
    rmdir rag_storage
    echo "  ✓ 移动 rag_storage/* -> data/storage/rag/"
else
    echo "  ⊘ rag_storage/ 为空或不存在，跳过"
fi
echo ""

# 4. 移动向量数据库
echo "[4/6] 移动向量数据库..."
if [ -d "backend/data/chroma" ] && [ "$(ls -A backend/data/chroma 2>/dev/null)" ]; then
    mv backend/data/chroma/* data/storage/vector_db/ 2>/dev/null || true
    rmdir backend/data/chroma
    rmdir backend/data 2>/dev/null || true
    echo "  ✓ 移动 backend/data/chroma/* -> data/storage/vector_db/"
else
    echo "  ⊘ backend/data/chroma/ 为空或不存在，跳过"
fi
echo ""

# 5. 移动用户上传目录
echo "[5/6] 移动用户上传目录..."
if [ -d "inputs" ]; then
    if [ ! -d "data/inputs" ]; then
        mv inputs data/
        echo "  ✓ 移动 inputs/ -> data/inputs/"
    else
        echo "  ⊘ data/inputs/ 已存在，跳过"
    fi
else
    mkdir -p data/inputs
    echo "  ✓ 创建 data/inputs/"
fi
echo ""

# 6. 移动日志文件
echo "[6/6] 移动日志文件..."
if ls *.log 1> /dev/null 2>&1; then
    mv *.log logs/ 2>/dev/null || true
    echo "  ✓ 移动 *.log -> logs/"
else
    echo "  ⊘ 根目录无日志文件，跳过"
fi
echo ""

# 7. 删除废弃目录
echo "[额外] 清理废弃目录..."
if [ -d "lightrag_data" ]; then
    rm -rf lightrag_data
    echo "  ✓ 删除 lightrag_data/"
else
    echo "  ⊘ lightrag_data/ 不存在，跳过"
fi
echo ""

echo "========================================="
echo "✅ 数据目录迁移完成！"
echo "========================================="
echo ""
echo "新的目录结构："
echo "data/"
echo "├── storage/"
echo "│   ├── graphs/      (原 data/graphs/)"
echo "│   ├── rag/         (原 rag_storage/)"
echo "│   └── vector_db/   (原 backend/data/chroma/)"
echo "├── inputs/          (原根目录 inputs/)"
echo "└── cache/"
echo ""
echo "logs/"
echo "└── *.log            (原根目录 *.log)"
echo ""
echo "⚠️  下一步："
echo "1. 更新配置文件和代码中的路径"
echo "2. 更新 .gitignore"
echo "3. 测试功能是否正常"
echo ""
