#!/bin/bash
# 检查英文数据脚本

echo "=== 检查 Neo4j 中的英文实体 ==="
echo ""
echo "请在 Neo4j Browser (http://localhost:7474) 中运行以下查询："
echo ""
echo "// 1. 查看所有实体（前 50 个）"
echo "MATCH (n:Entity) RETURN n.id, n.type LIMIT 50"
echo ""
echo "// 2. 搜索可能的英文实体（包含英文字母）"
echo "MATCH (n:Entity) WHERE n.id =~ '.*[a-zA-Z]+.*' RETURN n.id, n.type, n.doc_ids LIMIT 20"
echo ""
echo "// 3. 查看最近添加的文档"
echo "MATCH (n:Entity) RETURN DISTINCT n.doc_ids LIMIT 10"
echo ""
echo "// 4. 统计实体总数"
echo "MATCH (n:Entity) RETURN count(n) as total_entities"
echo ""
echo "=== 检查向量数据库中的数据 ==="
echo ""
echo "运行以下 Python 脚本："
echo ""
cat << 'EOF'
from backend.core.storage import get_vector_store

vector_store = get_vector_store()

# 查询所有文档片段
results = vector_store.collection.get(limit=10)
print(f"向量存储中的文档数量: {len(results['ids'])}")
print("\n前 10 个文档:")
for i, (doc_id, text) in enumerate(zip(results['ids'], results['documents'])):
    print(f"{i+1}. {doc_id}: {text[:100]}...")
EOF
