#!/usr/bin/env python3
"""处理整本书，提取知识图谱"""

import sys
import time

# 强制无缓冲输出
sys.stdout.reconfigure(line_buffering=True)

from backend.extraction import KnowledgeGraphExtractor
from backend.management import get_kg_manager

def main():
    extractor = KnowledgeGraphExtractor()
    kg_manager = get_kg_manager()

    print('=== 开始处理整本书 ===')
    print('文件: 让时间陪你慢慢变富.txt (160KB)')
    print('预计耗时: 10-15 分钟')
    print()
    sys.stdout.flush()

    start = time.time()

    result = extractor.extract_from_document('../tests/data/让时间陪你慢慢变富.txt')

    elapsed = time.time() - start
    print(f'\n=== 处理完成 ({elapsed:.1f}秒) ===')
    print(f'节点数: {len(result["nodes"])}')
    print(f'边数: {len(result["edges"])}')

    # 保存到 Neo4j
    doc_id = 'full_book_' + str(int(time.time()))
    stats = kg_manager.save_document(doc_id, result)
    print(f'\n已保存到 Neo4j: {stats}')

    # 显示度数最高的节点
    nodes_by_degree = sorted(result['nodes'], key=lambda n: n.get('degree', 0), reverse=True)
    print('\n=== Top 10 核心节点 ===')
    for node in nodes_by_degree[:10]:
        print(f'  {node["label"]} (degree={node.get("degree", 0)}, type={node.get("type", "?")})')

if __name__ == "__main__":
    main()
