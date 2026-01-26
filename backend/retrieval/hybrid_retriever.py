"""
Hybrid Retriever
混合检索模块

功能：
- 查询分类 (FACTUAL/EXPLORATORY/ANALYTICAL/RELATIONAL)
- KG 检索 (实体 + N跳邻居)
- RAG 检索 (语义相似)
- 结果融合
"""

import os
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

from openai import OpenAI
from dotenv import load_dotenv

from backend.management import get_kg_manager
from backend.core.storage import get_vector_store
from .prompts.qa_prompts import (
    QueryType,
    get_classification_prompt,
    get_entity_extraction_prompt,
    get_retrieval_strategy
)


load_dotenv()


class HybridRetriever:
    """混合检索器（使用 Neo4j）"""

    def __init__(self):
        """初始化混合检索器"""
        self.kg_manager = get_kg_manager()
        self.vector_store = get_vector_store()

        # LLM 客户端（用于查询分类和实体提取）
        api_base = os.getenv('LLM_BINDING_HOST', 'https://space.ai-builders.com/backend/v1')
        api_key = os.getenv('LLM_BINDING_API_KEY', '')
        self.model = os.getenv('LLM_MODEL', 'deepseek')

        self.client = OpenAI(
            base_url=api_base,
            api_key=api_key
        )

        self.top_k = int(os.getenv('RAG_TOP_K', '5'))

    def classify_query(self, question: str) -> QueryType:
        """
        分类查询类型

        Args:
            question: 用户问题

        Returns:
            QueryType 枚举值
        """
        prompt = get_classification_prompt(question)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是查询分类助手，只返回分类结果。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=20
            )

            result = response.choices[0].message.content.strip().upper()

            # 映射到 QueryType
            type_map = {
                "FACTUAL": QueryType.FACTUAL,
                "EXPLORATORY": QueryType.EXPLORATORY,
                "ANALYTICAL": QueryType.ANALYTICAL,
                "RELATIONAL": QueryType.RELATIONAL
            }

            return type_map.get(result, QueryType.ANALYTICAL)

        except Exception as e:
            print(f"查询分类失败: {e}")
            return QueryType.ANALYTICAL  # 默认混合策略

    def extract_entities_from_query(self, question: str) -> List[str]:
        """
        从问题中提取实体名称

        Args:
            question: 用户问题

        Returns:
            实体名称列表
        """
        prompt = get_entity_extraction_prompt(question)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是实体提取助手，只返回实体列表。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=100
            )

            result = response.choices[0].message.content.strip()

            if result == "无" or not result:
                return []

            # 分割实体
            entities = [e.strip() for e in result.split(",") if e.strip()]
            return entities

        except Exception as e:
            print(f"实体提取失败: {e}")
            return []

    def retrieve_from_kg(
        self,
        entities: List[str],
        n_hops: int = 1
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        从知识图谱检索

        Args:
            entities: 实体名称列表
            n_hops: 跳数（邻居深度）

        Returns:
            (相关实体列表, 相关关系列表)
        """
        all_graph = self.kg_manager.get_all_graphs()

        if not all_graph["nodes"]:
            return [], []

        # 构建图索引
        node_map = {node["id"]: node for node in all_graph["nodes"]}
        adjacency = defaultdict(list)  # node_id -> [(neighbor_id, edge)]

        for edge in all_graph["edges"]:
            source = edge.get("source")
            target = edge.get("target")
            if source and target:
                adjacency[source].append((target, edge))
                adjacency[target].append((source, edge))

        # 精确匹配实体
        matched_entities = set()
        for entity in entities:
            if entity in node_map:
                matched_entities.add(entity)
            else:
                # 模糊匹配
                for node_id in node_map:
                    if entity in node_id or node_id in entity:
                        matched_entities.add(node_id)

        if not matched_entities:
            # 尝试向量搜索实体
            for entity in entities:
                results = self.vector_store.search_entities(entity, top_k=2)
                for r in results:
                    if r.get("label") in node_map:
                        matched_entities.add(r["label"])

        if not matched_entities:
            return [], []

        # BFS 扩展 N 跳邻居
        visited = set(matched_entities)
        current_level = set(matched_entities)
        related_edges = []
        seen_edges = set()

        for _ in range(n_hops):
            next_level = set()
            for node_id in current_level:
                for neighbor_id, edge in adjacency[node_id]:
                    if neighbor_id not in visited:
                        next_level.add(neighbor_id)
                        visited.add(neighbor_id)

                    # 记录边
                    edge_key = f"{edge['source']}->{edge['target']}"
                    if edge_key not in seen_edges:
                        seen_edges.add(edge_key)
                        related_edges.append(edge)

            current_level = next_level

        # 构建结果
        related_entities = [
            node_map[node_id]
            for node_id in visited
            if node_id in node_map
        ]

        # 按度数排序
        related_entities.sort(key=lambda n: n.get("degree", 0), reverse=True)

        return related_entities, related_edges

    def retrieve_from_rag(
        self,
        question: str,
        top_k: Optional[int] = None
    ) -> List[Dict]:
        """
        从向量存储检索相似文档片段

        Args:
            question: 用户问题
            top_k: 返回数量

        Returns:
            相关文档片段列表
        """
        if top_k is None:
            top_k = self.top_k

        return self.vector_store.search_chunks(question, top_k=top_k)

    def retrieve(
        self,
        question: str,
        mode: str = "auto",
        n_hops: int = 1,
        top_k: Optional[int] = None
    ) -> Dict:
        """
        执行混合检索

        Args:
            question: 用户问题
            mode: 检索模式 ("auto", "kg_only", "rag_only", "hybrid", "kg_first", "rag_first")
            n_hops: KG 检索跳数
            top_k: RAG 检索数量

        Returns:
            检索结果字典
        """
        if top_k is None:
            top_k = self.top_k

        result = {
            "question": question,
            "query_type": None,
            "strategy": mode,
            "entities": [],
            "relations": [],
            "chunks": [],
            "extracted_entities": []
        }

        # 自动模式：先分类再决定策略
        if mode == "auto":
            query_type = self.classify_query(question)
            result["query_type"] = query_type.value
            mode = get_retrieval_strategy(query_type)
            result["strategy"] = mode

        # 提取问题中的实体
        extracted_entities = self.extract_entities_from_query(question)
        result["extracted_entities"] = extracted_entities

        # 根据策略执行检索
        if mode in ("kg_only", "kg_first", "hybrid"):
            entities, relations = self.retrieve_from_kg(extracted_entities, n_hops)
            result["entities"] = entities
            result["relations"] = relations

        if mode in ("rag_only", "rag_first", "hybrid"):
            chunks = self.retrieve_from_rag(question, top_k)
            result["chunks"] = chunks

        # kg_first 模式：如果 KG 结果不足，补充 RAG
        if mode == "kg_first" and len(result["entities"]) < 2:
            chunks = self.retrieve_from_rag(question, top_k)
            result["chunks"] = chunks

        # rag_first 模式：如果 RAG 结果不足，补充 KG
        if mode == "rag_first" and len(result["chunks"]) < 2:
            entities, relations = self.retrieve_from_kg(extracted_entities, n_hops)
            result["entities"] = entities
            result["relations"] = relations

        return result

    def get_entity_context(
        self,
        entity_name: str,
        n_hops: int = 2
    ) -> Dict:
        """
        获取实体的完整上下文

        Args:
            entity_name: 实体名称
            n_hops: 邻居跳数

        Returns:
            实体上下文信息
        """
        # 从 KG 获取实体和关系
        entities, relations = self.retrieve_from_kg([entity_name], n_hops)

        # 从 RAG 获取相关文档片段
        chunks = self.retrieve_from_rag(entity_name, top_k=3)

        # 找到主实体
        main_entity = None
        for e in entities:
            if e.get("id") == entity_name or e.get("label") == entity_name:
                main_entity = e
                break

        return {
            "entity": main_entity,
            "related_entities": [e for e in entities if e != main_entity],
            "relations": relations,
            "chunks": chunks
        }


# 单例
_retriever: Optional[HybridRetriever] = None


def get_retriever() -> HybridRetriever:
    """获取检索器实例（单例）"""
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever


# 命令行测试
if __name__ == "__main__":
    retriever = get_retriever()

    # 测试查询分类
    test_questions = [
        "李笑来是谁？",
        "介绍一下定投策略",
        "为什么要长期持有？",
        "李笑来和定投有什么关系？"
    ]

    for q in test_questions:
        query_type = retriever.classify_query(q)
        entities = retriever.extract_entities_from_query(q)
        print(f"问题: {q}")
        print(f"  类型: {query_type.value}")
        print(f"  实体: {entities}")
        print()

    # 测试混合检索
    print("=== 测试混合检索 ===")
    result = retriever.retrieve("李笑来的投资理念是什么？", mode="auto")
    print(f"问题: {result['question']}")
    print(f"查询类型: {result['query_type']}")
    print(f"策略: {result['strategy']}")
    print(f"提取实体: {result['extracted_entities']}")
    print(f"KG 实体数: {len(result['entities'])}")
    print(f"KG 关系数: {len(result['relations'])}")
    print(f"RAG 片段数: {len(result['chunks'])}")
