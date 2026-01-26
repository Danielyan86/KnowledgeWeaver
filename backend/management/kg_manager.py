"""
Knowledge Graph Management
知识图谱统一管理接口

核心功能：
- 统一管理 Neo4j 存储
- 自动降级处理
- 规范化集成
"""

import os
from typing import Dict, Optional, List
from dotenv import load_dotenv

from backend.core.storage.neo4j import get_neo4j_storage
from backend.extraction.normalizer import KnowledgeGraphNormalizer


# 加载环境变量
load_dotenv()


class KnowledgeGraphManager:
    """知识图谱统一管理接口（Neo4j）"""

    def __init__(self, use_neo4j: bool = None):
        """
        初始化管理器

        Args:
            use_neo4j: 是否使用 Neo4j，None 时从环境变量读取
        """
        # 规范化器
        self.normalizer = KnowledgeGraphNormalizer()

        # Neo4j 存储
        if use_neo4j is None:
            use_neo4j = os.getenv('USE_NEO4J', 'true').lower() == 'true'

        self.neo4j_storage = None
        if use_neo4j:
            try:
                self.neo4j_storage = get_neo4j_storage()
                if self.neo4j_storage:
                    print("✓ Neo4j 存储已启用")
                else:
                    print("⚠ Neo4j 连接失败")
            except Exception as e:
                print(f"⚠ Neo4j 初始化失败: {e}")

    def save_document(self, doc_id: str, raw_graph: Dict,
                     metadata: Dict = None) -> Dict:
        """
        保存文档（规范化 + Neo4j 存储）

        Args:
            doc_id: 文档 ID
            raw_graph: 原始图谱数据
            metadata: 元数据

        Returns:
            保存统计信息
        """
        # 1. 规范化（如果尚未规范化）
        if "stats" not in raw_graph:
            normalized = self.normalizer.normalize_graph(raw_graph)
        else:
            normalized = raw_graph

        # 2. 保存到 Neo4j
        neo4j_stats = {}
        if self.neo4j_storage:
            try:
                neo4j_stats = self.neo4j_storage.save_graph_batch(normalized, doc_id)
                print(f"✓ Neo4j 保存成功: {neo4j_stats.get('nodes_created', 0)} 节点, {neo4j_stats.get('edges_created', 0)} 边")
            except Exception as e:
                print(f"✗ Neo4j 写入失败: {e}")
                neo4j_stats = {"error": str(e)}
        else:
            neo4j_stats = {"error": "Neo4j 未启用"}

        return {
            "normalization": normalized.get("stats", {}),
            "neo4j": neo4j_stats
        }

    def load_document(self, doc_id: str) -> Optional[Dict]:
        """
        加载文档（从 Neo4j）

        Args:
            doc_id: 文档 ID

        Returns:
            图谱数据
        """
        if not self.neo4j_storage:
            return {"nodes": [], "edges": [], "error": "Neo4j 未启用"}

        try:
            # 查询该文档的所有节点和边
            with self.neo4j_storage.driver.session() as session:
                # 查询节点
                nodes_result = session.run("""
                    MATCH (n:Entity)
                    WHERE $doc_id IN n.doc_ids
                    RETURN n.id as id, n.label as label, n.type as type,
                           n.description as description, n.doc_ids as doc_ids
                """, doc_id=doc_id)

                nodes = [dict(record) for record in nodes_result]

                # 查询边
                edges_result = session.run("""
                    MATCH (s:Entity)-[r {doc_id: $doc_id}]->(t:Entity)
                    RETURN s.id as source, t.id as target,
                           COALESCE(r.label, type(r)) as label, r.weight as weight
                """, doc_id=doc_id)

                edges = [dict(record) for record in edges_result]

                return {"nodes": nodes, "edges": edges}

        except Exception as e:
            print(f"从 Neo4j 加载失败: {e}")
            return {"nodes": [], "edges": [], "error": str(e)}

    def list_documents(self) -> List[Dict]:
        """
        列出所有文档

        Returns:
            文档列表
        """
        if not self.neo4j_storage:
            return []

        try:
            with self.neo4j_storage.driver.session() as session:
                result = session.run("""
                    MATCH (n:Entity)
                    UNWIND n.doc_ids as doc_id
                    WITH doc_id, count(n) as node_count
                    RETURN doc_id, node_count
                    ORDER BY doc_id DESC
                """)

                docs = []
                for record in result:
                    docs.append({
                        "doc_id": record["doc_id"],
                        "node_count": record["node_count"],
                        "edge_count": 0,  # TODO: 查询边数
                        "updated_at": "N/A"
                    })

                return docs

        except Exception as e:
            print(f"列出文档失败: {e}")
            return []

    def delete_document(self, doc_id: str) -> Dict:
        """
        删除文档

        Args:
            doc_id: 文档 ID

        Returns:
            删除统计信息
        """
        if not self.neo4j_storage:
            return {"error": "Neo4j 未启用"}

        try:
            stats = self.neo4j_storage.delete_by_doc(doc_id)
            print(f"✓ 已删除文档 {doc_id}: {stats.get('nodes_deleted', 0)} 节点, {stats.get('edges_deleted', 0)} 边")
            return {"neo4j": stats}
        except Exception as e:
            print(f"从 Neo4j 删除失败: {e}")
            return {"error": str(e)}

    def get_stats(self) -> Dict:
        """
        获取统计信息

        Returns:
            统计信息
        """
        if not self.neo4j_storage:
            return {"error": "Neo4j 未启用"}

        try:
            stats = self.neo4j_storage.get_stats()
            return {"neo4j": stats}
        except Exception as e:
            return {"error": str(e)}

    def get_all_graphs(self) -> Dict:
        """
        获取全部图谱数据

        Returns:
            图谱数据
        """
        if not self.neo4j_storage:
            return {"nodes": [], "edges": []}

        try:
            with self.neo4j_storage.driver.session() as session:
                # 查询所有节点
                nodes_result = session.run("""
                    MATCH (n:Entity)
                    RETURN n.id as id, n.label as label, n.type as type,
                           n.description as description,
                           size(n.doc_ids) as doc_count
                    LIMIT 1000
                """)

                nodes = [{
                    "id": record["id"],
                    "label": record["label"],
                    "type": record["type"],
                    "description": record["description"],
                    "degree": 0  # 将在计算边后更新
                } for record in nodes_result]

                # 查询所有边
                edges_result = session.run("""
                    MATCH (s:Entity)-[r]->(t:Entity)
                    RETURN DISTINCT s.id as source, t.id as target,
                           COALESCE(r.label, type(r)) as label
                    LIMIT 5000
                """)

                edges = [{
                    "source": record["source"],
                    "target": record["target"],
                    "label": record["label"],
                    "weight": 1
                } for record in edges_result]

                # 计算节点度数
                degree_map = {}
                for edge in edges:
                    degree_map[edge["source"]] = degree_map.get(edge["source"], 0) + 1
                    degree_map[edge["target"]] = degree_map.get(edge["target"], 0) + 1

                for node in nodes:
                    node["degree"] = degree_map.get(node["id"], 0)

                return {"nodes": nodes, "edges": edges}

        except Exception as e:
            print(f"查询全部图谱失败: {e}")
            return {"nodes": [], "edges": []}

    def get_graph_by_label(self, label: str) -> Dict:
        """
        按标签查询子图

        Args:
            label: 节点标签

        Returns:
            子图数据
        """
        return self.query_subgraph(label, n_hops=2)

    def get_popular_labels(self, limit: int = 30) -> List[str]:
        """
        获取热门标签

        Args:
            limit: 返回数量

        Returns:
            标签列表
        """
        if not self.neo4j_storage:
            return []

        try:
            with self.neo4j_storage.driver.session() as session:
                result = session.run("""
                    MATCH (n:Entity)
                    OPTIONAL MATCH (n)-[r]-()
                    WITH n, count(r) as degree
                    RETURN n.id as id
                    ORDER BY degree DESC, n.id
                    LIMIT $limit
                """, limit=limit)

                return [record["id"] for record in result]

        except Exception as e:
            print(f"获取热门标签失败: {e}")
            return []

    def query_subgraph(self, entity_id: str, n_hops: int = 1) -> Dict:
        """
        查询实体子图

        Args:
            entity_id: 实体 ID
            n_hops: 跳数

        Returns:
            子图数据
        """
        if not self.neo4j_storage:
            return {"nodes": [], "edges": []}

        try:
            return self.neo4j_storage.query_subgraph(entity_id, n_hops)
        except Exception as e:
            print(f"Neo4j 查询失败: {e}")
            return {"nodes": [], "edges": []}


# 单例实例
_manager_instance = None


def get_kg_manager(use_neo4j: bool = None) -> KnowledgeGraphManager:
    """
    获取知识图谱管理器实例（单例模式）

    Args:
        use_neo4j: 是否使用 Neo4j

    Returns:
        KnowledgeGraphManager 实例
    """
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = KnowledgeGraphManager(use_neo4j)
    return _manager_instance


# 命令行测试
if __name__ == "__main__":
    manager = get_kg_manager()
    print("知识图谱管理器初始化成功")
    print("统计信息:", manager.get_stats())
