"""
Knowledge Graph Extractor
知识图谱提取器

核心功能：
- 调用 LLM 提取实体和关系
- 文档分块处理
- 合并多个块的提取结果
"""

import json
import re
import os
from typing import Dict, List, Optional
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

from ..retrieval.prompts import get_extraction_prompt, NODE_TYPES
from .normalizer import KnowledgeGraphNormalizer
from ..core.observability import get_tracer


# 加载环境变量
load_dotenv()


class KnowledgeGraphExtractor:
    """知识图谱提取器"""

    def __init__(self, chunk_size: int = 800):
        """
        初始化提取器

        Args:
            chunk_size: 文档分块大小（字符数）
        """
        self.chunk_size = chunk_size
        self.normalizer = KnowledgeGraphNormalizer()

        # 从环境变量读取 LLM 配置
        api_base = os.getenv('LLM_BINDING_HOST', 'https://space.ai-builders.com/backend/v1')
        api_key = os.getenv('LLM_BINDING_API_KEY', '')
        self.model = os.getenv('LLM_MODEL', 'deepseek')

        # 创建 OpenAI 客户端
        client = OpenAI(
            base_url=api_base,
            api_key=api_key
        )

        # 使用 Langfuse wrapper 包装客户端（自动追踪所有 LLM 调用）
        tracer = get_tracer()
        self.client = tracer.wrap_openai(client)

    def chunk_text(self, text: str) -> List[str]:
        """
        将文本分割成块

        Args:
            text: 原始文本

        Returns:
            文本块列表
        """
        if not text:
            return []

        # 按段落分割
        paragraphs = re.split(r'\n\s*\n', text)

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # 如果当前段落加上已有内容超过限制，先保存当前块
            if len(current_chunk) + len(para) > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""

            # 如果单个段落就超过限制，按句子分割
            if len(para) > self.chunk_size:
                sentences = re.split(r'([。！？.!?])', para)
                temp = ""
                for i in range(0, len(sentences) - 1, 2):
                    sentence = sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else "")
                    if len(temp) + len(sentence) > self.chunk_size and temp:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            current_chunk = ""
                        chunks.append(temp.strip())
                        temp = ""
                    temp += sentence

                if temp:
                    current_chunk += temp
            else:
                current_chunk += para + "\n\n"

        # 添加最后一个块
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _parse_llm_response(self, response_text: str) -> Dict:
        """
        解析 LLM 响应，提取 JSON

        Args:
            response_text: LLM 的原始响应

        Returns:
            解析后的字典，包含 entities 和 relations
        """
        # 尝试找到 JSON 代码块
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接解析
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                json_str = json_match.group(0)
            else:
                return {"entities": [], "relations": []}

        try:
            result = json.loads(json_str)
            return {
                "entities": result.get("entities", []),
                "relations": result.get("relations", [])
            }
        except json.JSONDecodeError:
            return {"entities": [], "relations": []}

    def extract_from_text(self, text: str) -> Dict:
        """
        从文本中提取实体和关系

        Args:
            text: 待提取的文本

        Returns:
            提取结果字典，包含 entities 和 relations
        """
        prompt = get_extraction_prompt(text)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个知识图谱提取专家，请严格按照JSON格式输出。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # 低温度以获得更稳定的输出
                max_tokens=2000
            )

            response_text = response.choices[0].message.content
            return self._parse_llm_response(response_text)

        except Exception as e:
            print(f"LLM 调用失败: {e}")
            return {"entities": [], "relations": []}

    def merge_graphs(self, graphs: List[Dict], connect_islands: bool = True) -> Dict:
        """
        合并多个提取结果

        Args:
            graphs: 多个提取结果列表
            connect_islands: 是否尝试连接孤岛

        Returns:
            合并后的图谱数据
        """
        all_entities = {}  # name -> entity
        all_relations = []
        seen_relations = set()

        for graph in graphs:
            # 合并实体
            for entity in graph.get("entities", []):
                name = entity.get("name", "").strip()
                if not name:
                    continue

                if name not in all_entities:
                    all_entities[name] = {
                        "name": name,
                        "type": entity.get("type", "Entity"),
                        "description": entity.get("description", "")
                    }
                else:
                    # 合并描述
                    existing = all_entities[name]
                    if entity.get("description") and not existing.get("description"):
                        existing["description"] = entity.get("description")

            # 合并关系
            for relation in graph.get("relations", []):
                source = relation.get("source", "").strip()
                target = relation.get("target", "").strip()
                rel = relation.get("relation", "").strip()

                if not source or not target or not rel:
                    continue

                # 去重
                rel_key = f"{source}-{rel}->{target}"
                if rel_key not in seen_relations:
                    seen_relations.add(rel_key)
                    all_relations.append({
                        "source": source,
                        "relation": rel,
                        "target": target
                    })

        # 尝试连接孤岛
        if connect_islands:
            all_relations = self._connect_island_nodes(
                all_entities, all_relations, seen_relations
            )

        return {
            "entities": list(all_entities.values()),
            "relations": all_relations
        }

    def _find_connected_components(self, relations: List[Dict], all_nodes: set) -> List[set]:
        """
        使用并查集找出所有连通分量

        Args:
            relations: 关系列表
            all_nodes: 所有节点集合

        Returns:
            连通分量列表，每个分量是节点集合
        """
        # 并查集
        parent = {node: node for node in all_nodes}

        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        # 合并有边连接的节点
        for rel in relations:
            source, target = rel["source"], rel["target"]
            if source in all_nodes and target in all_nodes:
                union(source, target)

        # 按根节点分组
        components = {}
        for node in all_nodes:
            root = find(node)
            if root not in components:
                components[root] = set()
            components[root].add(node)

        return list(components.values())

    def _connect_island_nodes(
        self,
        entities: Dict,
        relations: List[Dict],
        seen_relations: set
    ) -> List[Dict]:
        """
        尝试连接孤岛节点/孤立连通分量到主图

        策略：
        1. 使用并查集找出所有连通分量
        2. 找出最大的连通分量作为主图
        3. 将其他孤立分量连接到主图

        Args:
            entities: 实体字典
            relations: 关系列表
            seen_relations: 已见关系集合

        Returns:
            更新后的关系列表
        """
        all_nodes = set(entities.keys())

        if not all_nodes:
            return relations

        # 找出所有连通分量
        components = self._find_connected_components(relations, all_nodes)

        if len(components) <= 1:
            # 只有一个或零个连通分量，无需连接
            return relations

        # 计算每个节点的度数
        degree_map = {}
        for rel in relations:
            degree_map[rel["source"]] = degree_map.get(rel["source"], 0) + 1
            degree_map[rel["target"]] = degree_map.get(rel["target"], 0) + 1

        # 按大小排序，最大的是主图
        components.sort(key=lambda c: len(c), reverse=True)
        main_component = components[0]
        island_components = components[1:]

        # 找出主图的核心节点（度数最高的几个）
        main_nodes_with_degree = [
            (node, degree_map.get(node, 0))
            for node in main_component
        ]
        main_nodes_with_degree.sort(key=lambda x: x[1], reverse=True)
        core_nodes = [node for node, _ in main_nodes_with_degree[:3]]

        if not core_nodes:
            core_nodes = list(main_component)[:1]

        print(f"  主图核心节点: {core_nodes}")
        print(f"  孤立分量数: {len(island_components)}")

        # 为每个孤立分量建立到主图的连接
        new_relations = list(relations)

        for island_comp in island_components:
            # 找出孤立分量中度数最高的节点作为连接点
            island_nodes_with_degree = [
                (node, degree_map.get(node, 0))
                for node in island_comp
            ]
            island_nodes_with_degree.sort(key=lambda x: x[1], reverse=True)
            island_connector = island_nodes_with_degree[0][0]

            island_entity = entities.get(island_connector, {})
            island_type = island_entity.get("type", "Entity")

            connected = False

            # 策略1: 同类型节点连接
            for core in core_nodes:
                core_entity = entities.get(core, {})
                core_type = core_entity.get("type", "Entity")

                if island_type == core_type:
                    rel_key = f"{island_connector}-相关->{core}"
                    if rel_key not in seen_relations:
                        seen_relations.add(rel_key)
                        new_relations.append({
                            "source": island_connector,
                            "relation": "相关",
                            "target": core
                        })
                        print(f"  连接: {island_connector} -[相关]-> {core}")
                        connected = True
                        break

            # 策略2: 如果还没连接，连接到度数最高的核心节点
            if not connected and core_nodes:
                core = core_nodes[0]
                rel_key = f"{island_connector}-提及->{core}"
                if rel_key not in seen_relations:
                    seen_relations.add(rel_key)
                    new_relations.append({
                        "source": island_connector,
                        "relation": "提及",
                        "target": core
                    })
                    print(f"  连接: {island_connector} -[提及]-> {core}")

        return new_relations

    def _convert_to_graph_format(self, extracted: Dict) -> Dict:
        """
        将 LLM 提取的数据转换为前端期望的格式

        Args:
            extracted: LLM 提取的原始数据

        Returns:
            前端格式的图谱数据
        """
        # 构建节点
        nodes = []
        node_ids = set()

        for entity in extracted.get("entities", []):
            name = entity.get("name", "").strip()
            if not name or name in node_ids:
                continue

            node_ids.add(name)
            nodes.append({
                "id": name,
                "label": name,
                "type": entity.get("type", "Entity"),
                "description": entity.get("description", ""),
                "properties": {},
                "degree": 0
            })

        # 构建边，并确保端点节点存在
        edges = []
        for relation in extracted.get("relations", []):
            source = relation.get("source", "").strip()
            target = relation.get("target", "").strip()
            rel = relation.get("relation", "").strip()

            if not source or not target or source == target:
                continue

            # 确保源节点存在
            if source not in node_ids:
                node_ids.add(source)
                nodes.append({
                    "id": source,
                    "label": source,
                    "type": "Entity",
                    "description": "",
                    "properties": {},
                    "degree": 0
                })

            # 确保目标节点存在
            if target not in node_ids:
                node_ids.add(target)
                nodes.append({
                    "id": target,
                    "label": target,
                    "type": "Entity",
                    "description": "",
                    "properties": {},
                    "degree": 0
                })

            edges.append({
                "source": source,
                "target": target,
                "label": rel,
                "weight": 1
            })

        # 计算节点度数
        degree_map = {}
        for edge in edges:
            degree_map[edge["source"]] = degree_map.get(edge["source"], 0) + 1
            degree_map[edge["target"]] = degree_map.get(edge["target"], 0) + 1

        for node in nodes:
            node["degree"] = degree_map.get(node["id"], 0)

        return {"nodes": nodes, "edges": edges}

    def _extract_document_topic(self, text: str) -> str:
        """
        提取文档主题/核心实体

        Args:
            text: 文档文本（取前1000字）

        Returns:
            文档主题描述
        """
        sample = text[:1000] if len(text) > 1000 else text

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是文档分析专家。"},
                    {"role": "user", "content": f"""请用一句话总结这篇文档的主题和核心实体（人物、概念等）。

文档开头：
{sample}

回答格式：本文主要讨论[主题]，核心实体包括[实体1]、[实体2]等。"""}
                ],
                temperature=0.1,
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return ""

    def extract_from_document(self, file_path: str, return_chunks: bool = False) -> Dict:
        """
        从文档中提取知识图谱

        Args:
            file_path: 文档路径
            return_chunks: 是否返回原始 chunks（用于 RAG 索引）

        Returns:
            提取并规范化后的图谱数据，如果 return_chunks=True，还包含 chunks 字段
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 读取文件内容
        if path.suffix.lower() == '.txt':
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
        elif path.suffix.lower() == '.pdf':
            # TODO: 支持 PDF 解析
            raise NotImplementedError("PDF 解析尚未实现")
        else:
            raise ValueError(f"不支持的文件格式: {path.suffix}")

        # 提取文档主题（用于提供上下文）
        doc_topic = self._extract_document_topic(text)
        if doc_topic:
            print(f"文档主题: {doc_topic}")

        # 分块
        chunks = self.chunk_text(text)
        print(f"文档分成 {len(chunks)} 个块")

        # 收集前几个块的核心实体作为上下文
        core_entities = set()
        graphs = []

        for i, chunk in enumerate(chunks):
            print(f"正在处理第 {i + 1}/{len(chunks)} 块...")

            # 构建带上下文的提取提示
            context = ""
            if doc_topic:
                context += f"文档背景：{doc_topic}\n"
            if core_entities:
                context += f"已识别的核心实体：{', '.join(list(core_entities)[:10])}\n"
                context += "请注意：如果当前文本与这些实体相关，请建立关系连接。\n\n"

            result = self.extract_from_text(context + chunk if context else chunk)

            if result["entities"] or result["relations"]:
                graphs.append(result)
                # 收集高频实体
                for entity in result.get("entities", []):
                    name = entity.get("name", "")
                    if name and len(name) <= 10:
                        core_entities.add(name)

        # 合并结果（包括孤岛连接）
        merged = self.merge_graphs(graphs, connect_islands=True)
        print(f"合并后：{len(merged['entities'])} 个实体，{len(merged['relations'])} 个关系")

        # 转换为前端格式
        graph_data = self._convert_to_graph_format(merged)

        # 规范化
        normalized = self.normalizer.normalize_graph(graph_data)
        print(f"规范化后：{normalized['stats']}")

        # 如果需要返回 chunks 用于 RAG 索引
        if return_chunks:
            normalized["chunks"] = chunks
            normalized["doc_topic"] = doc_topic

        return normalized


# 命令行测试
if __name__ == "__main__":
    import sys

    extractor = KnowledgeGraphExtractor()

    if len(sys.argv) > 1:
        # 处理文件
        file_path = sys.argv[1]
        result = extractor.extract_from_document(file_path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 测试文本
        test_text = """
        李笑来在《让时间陪你慢慢变富》中主张定投策略。
        他认为定投是最适合普通人的投资方式，推荐标普500指数基金。
        长期主义是这本书的核心理念，强调时间复利的重要性。
        """
        result = extractor.extract_from_text(test_text)
        graph = extractor._convert_to_graph_format(result)
        normalized = extractor.normalizer.normalize_graph(graph)
        print(json.dumps(normalized, ensure_ascii=False, indent=2))
