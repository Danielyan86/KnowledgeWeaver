"""
Bilingual Integration Example
双语集成示例

演示中英文文档的实体提取和关系规范化全流程
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.extraction.entity_filter import EntityFilter
from backend.extraction.normalizer import KnowledgeGraphNormalizer


def process_chinese_example():
    """处理中文示例"""
    print("\n" + "=" * 60)
    print("中文文档处理示例")
    print("=" * 60)

    # 模拟从 LLM 提取的原始图谱数据
    raw_graph = {
        "entities": [
            {"name": "李笑来", "type": "Person"},
            {"name": "让时间陪你慢慢变富", "type": "Book"},
            {"name": "定投", "type": "Strategy"},
            {"name": "普通人", "type": "Group"},
            {"name": "这个", "type": "Entity"},  # 停用词
        ],
        "relations": [
            {"source": "李笑来", "relation": "著作", "target": "让时间陪你慢慢变富"},
            {"source": "让时间陪你慢慢变富", "relation": "主张", "target": "定投"},
            {"source": "定投", "relation": "适用于", "target": "普通人"},
            {"source": "这个", "relation": "相关", "target": "定投"},  # 包含停用词
        ]
    }

    # 步骤 1: 实体过滤
    filter = EntityFilter()
    filtered_graph = filter.filter_graph(raw_graph)

    print("\n步骤 1: 实体过滤")
    print(f"原始实体数: {len(raw_graph['entities'])}")
    print(f"过滤后实体数: {len(filtered_graph['entities'])}")
    print("保留的实体:", [e['name'] for e in filtered_graph['entities']])

    # 步骤 2: 规范化
    normalizer = KnowledgeGraphNormalizer()
    normalized_graph = normalizer.normalize_graph({
        "nodes": [{"id": e["name"], "type": e["type"]} for e in filtered_graph["entities"]],
        "edges": [{"source": r["source"], "target": r["target"], "label": r["relation"]}
                  for r in filtered_graph["relations"]]
    })

    print("\n步骤 2: 图谱规范化")
    print(f"规范化后节点数: {len(normalized_graph['nodes'])}")
    print(f"规范化后关系数: {len(normalized_graph['edges'])}")

    print("\n最终节点:")
    for node in normalized_graph['nodes']:
        print(f"  - {node['id']} ({node['type']})")

    print("\n最终关系:")
    for edge in normalized_graph['edges']:
        print(f"  - {edge['source']} -[{edge['label']}]-> {edge['target']}")


def process_english_example():
    """处理英文示例"""
    print("\n" + "=" * 60)
    print("英文文档处理示例")
    print("=" * 60)

    # 模拟从 LLM 提取的原始图谱数据
    raw_graph = {
        "entities": [
            {"name": "Warren Buffett", "type": "Person"},
            {"name": "The Intelligent Investor", "type": "Book"},
            {"name": "value investing", "type": "Strategy"},
            {"name": "long-term investors", "type": "Group"},
            {"name": "the", "type": "Entity"},  # 停用词
        ],
        "relations": [
            {"source": "Warren Buffett", "relation": "wrote", "target": "The Intelligent Investor"},
            {"source": "The Intelligent Investor", "relation": "recommends", "target": "value investing"},
            {"source": "value investing", "relation": "suitable_for", "target": "long-term investors"},
            {"source": "the", "relation": "relates", "target": "value investing"},  # 包含停用词
        ]
    }

    # 步骤 1: 实体过滤
    filter = EntityFilter()
    filtered_graph = filter.filter_graph(raw_graph)

    print("\n步骤 1: 实体过滤")
    print(f"原始实体数: {len(raw_graph['entities'])}")
    print(f"过滤后实体数: {len(filtered_graph['entities'])}")
    print("保留的实体:", [e['name'] for e in filtered_graph['entities']])

    # 步骤 2: 规范化
    normalizer = KnowledgeGraphNormalizer()
    normalized_graph = normalizer.normalize_graph({
        "nodes": [{"id": e["name"], "type": e["type"]} for e in filtered_graph["entities"]],
        "edges": [{"source": r["source"], "target": r["target"], "label": r["relation"]}
                  for r in filtered_graph["relations"]]
    })

    print("\n步骤 2: 图谱规范化")
    print(f"规范化后节点数: {len(normalized_graph['nodes'])}")
    print(f"规范化后关系数: {len(normalized_graph['edges'])}")

    print("\n最终节点:")
    for node in normalized_graph['nodes']:
        print(f"  - {node['id']} ({node['type']})")

    print("\n最终关系:")
    for edge in normalized_graph['edges']:
        print(f"  - {edge['source']} -[{edge['label']}]-> {edge['target']}")


def process_bilingual_example():
    """处理中英文混合示例"""
    print("\n" + "=" * 60)
    print("中英文混合文档处理示例")
    print("=" * 60)

    # 模拟从 LLM 提取的原始图谱数据
    raw_graph = {
        "entities": [
            {"name": "Warren Buffett", "type": "Person"},
            {"name": "价值投资", "type": "Concept"},
            {"name": "The Intelligent Investor", "type": "Book"},
            {"name": "长期主义", "type": "Concept"},
            {"name": "it", "type": "Entity"},  # 英文停用词
            {"name": "这", "type": "Entity"},  # 中文停用词
        ],
        "relations": [
            {"source": "Warren Buffett", "relation": "recommends", "target": "价值投资"},
            {"source": "The Intelligent Investor", "relation": "主张", "target": "长期主义"},
            {"source": "价值投资", "relation": "requires", "target": "长期主义"},
        ]
    }

    # 步骤 1: 实体过滤
    filter = EntityFilter()
    filtered_graph = filter.filter_graph(raw_graph)

    print("\n步骤 1: 实体过滤")
    print(f"原始实体数: {len(raw_graph['entities'])}")
    print(f"过滤后实体数: {len(filtered_graph['entities'])}")
    print("保留的实体:", [e['name'] for e in filtered_graph['entities']])

    # 步骤 2: 规范化
    normalizer = KnowledgeGraphNormalizer()
    normalized_graph = normalizer.normalize_graph({
        "nodes": [{"id": e["name"], "type": e["type"]} for e in filtered_graph["entities"]],
        "edges": [{"source": r["source"], "target": r["target"], "label": r["relation"]}
                  for r in filtered_graph["relations"]]
    })

    print("\n步骤 2: 图谱规范化")
    print(f"规范化后节点数: {len(normalized_graph['nodes'])}")
    print(f"规范化后关系数: {len(normalized_graph['edges'])}")

    print("\n最终节点:")
    for node in normalized_graph['nodes']:
        print(f"  - {node['id']} ({node['type']})")

    print("\n最终关系:")
    for edge in normalized_graph['edges']:
        print(f"  - {edge['source']} -[{edge['label']}]-> {edge['target']}")


if __name__ == "__main__":
    print("=" * 60)
    print("KnowledgeWeaver 双语处理集成示例")
    print("=" * 60)

    process_chinese_example()
    process_english_example()
    process_bilingual_example()

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)
