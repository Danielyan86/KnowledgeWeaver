"""
Neo4j Storage Adapter
Neo4j 存储适配器

核心功能：
- 批量保存图谱数据到 Neo4j
- 高性能图遍历和查询
- 自动索引管理
"""

import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("警告: neo4j 包未安装，Neo4j 功能将不可用")


# 加载环境变量
load_dotenv()


# 中文关系类型到 Neo4j 关系类型的映射
RELATION_TYPE_MAPPING = {
    # 创作关系
    '著作': 'AUTHORED',
    '编写': 'WROTE',
    '撰写': 'COMPOSED',
    '创作': 'CREATED',
    '出版': 'PUBLISHED',

    # 主张/观点关系
    '主张': 'ADVOCATES',
    '强调': 'EMPHASIZES',
    '提倡': 'PROMOTES',
    '倡导': 'CHAMPIONS',
    '认为': 'BELIEVES',

    # 包含/属于关系
    '属于': 'BELONGS_TO',
    '包含': 'CONTAINS',
    '涵盖': 'COVERS',
    '包括': 'INCLUDES',

    # 适用关系
    '适用于': 'APPLIES_TO',
    '适合': 'SUITS',
    '针对': 'TARGETS',
    '面向': 'ORIENTED_TO',

    # 影响关系
    '影响': 'AFFECTS',
    '导致': 'CAUSES',
    '产生': 'GENERATES',
    '带来': 'BRINGS',

    # 依赖关系
    '依赖': 'DEPENDS_ON',
    '基于': 'BASED_ON',
    '建立在': 'BUILT_ON',
    '需要': 'REQUIRES',

    # 推荐关系
    '推荐': 'RECOMMENDS',
    '建议': 'SUGGESTS',

    # 特征关系
    '特点': 'CHARACTERIZED_BY',
    '特征': 'FEATURED_BY',

    # 对比关系
    '对比': 'CONTRASTS',
    '相比': 'COMPARED_TO',
    '区别': 'DIFFERS_FROM',

    # 反例关系
    '反例': 'COUNTER_EXAMPLE',
    '不推荐': 'NOT_RECOMMENDED',

    # 其他常见关系
    '投资': 'INVESTS_IN',
    '降低': 'REDUCES',
    '提高': 'INCREASES',
    '提供': 'PROVIDES',
    '获得': 'OBTAINS',
    '实现': 'ACHIEVES',
    '联系': 'RELATES_TO',
    '定期': 'PERIODIC',
    '定额': 'FIXED_AMOUNT',
}


def normalize_relation_type(chinese_relation: str) -> str:
    """
    将中文关系类型转换为 Neo4j 兼容的英文关系类型

    Args:
        chinese_relation: 中文关系名称

    Returns:
        英文关系类型（大写，下划线分隔）
    """
    # 去除空格
    relation = chinese_relation.strip()

    # 如果已经在映射表中，直接返回
    if relation in RELATION_TYPE_MAPPING:
        return RELATION_TYPE_MAPPING[relation]

    # 默认使用 RELATES
    return 'RELATES'


class Neo4jStorage:
    """Neo4j 存储适配器"""

    def __init__(self):
        """
        初始化 Neo4j 连接
        所有配置从环境变量读取
        """
        if not NEO4J_AVAILABLE:
            raise ImportError("需要安装 neo4j 包: pip install neo4j")

        # 从环境变量读取配置
        uri = os.getenv('NEO4J_URI')
        user = os.getenv('NEO4J_USER')
        password = os.getenv('NEO4J_PASSWORD')

        if not all([uri, user, password]):
            raise ValueError("请在 .env 中配置 NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")

        # 连接池大小
        max_pool_size = int(os.getenv('NEO4J_MAX_POOL_SIZE', '50'))

        self.driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            max_connection_pool_size=max_pool_size
        )

    def save_graph_batch(self, graph_data: Dict, doc_id: str,
                         overwrite: bool = True) -> Dict:
        """
        批量保存图谱（优化性能）

        Args:
            graph_data: 图谱数据，包含 nodes 和 edges
            doc_id: 文档 ID
            overwrite: 是否覆盖已存在的文档数据（默认 True）

        Returns:
            保存统计信息
        """
        batch_size = int(os.getenv('NEO4J_BATCH_SIZE', '500'))
        stats = {"nodes_created": 0, "edges_created": 0, "failed": 0,
                "deleted_nodes": 0, "deleted_edges": 0}

        with self.driver.session() as session:
            with session.begin_transaction() as tx:
                # 如果覆盖模式，先删除该文档的旧数据
                if overwrite:
                    try:
                        # 1. 删除该文档的所有关系
                        result_edges = tx.run("""
                            MATCH ()-[r {doc_id: $doc_id}]->()
                            DELETE r
                            RETURN count(r) as deleted
                        """, doc_id=doc_id)
                        stats["deleted_edges"] = result_edges.single()["deleted"]

                        # 2. 从节点的 doc_ids 数组中移除该 doc_id
                        tx.run("""
                            MATCH (n:Entity)
                            WHERE $doc_id IN n.doc_ids
                            SET n.doc_ids = [x IN n.doc_ids WHERE x <> $doc_id]
                        """, doc_id=doc_id)

                        # 3. 删除 doc_ids 为空的孤立节点
                        result_nodes = tx.run("""
                            MATCH (n:Entity)
                            WHERE size(n.doc_ids) = 0
                            DELETE n
                            RETURN count(n) as deleted
                        """)
                        stats["deleted_nodes"] = result_nodes.single()["deleted"]

                        if stats["deleted_edges"] > 0 or stats["deleted_nodes"] > 0:
                            print(f"  已删除旧数据: {stats['deleted_nodes']} 个节点, {stats['deleted_edges']} 条边")
                    except Exception as e:
                        print(f"删除旧数据失败: {e}")
                # 批量创建节点
                # 注意：节点可能跨文档共享，所以 doc_ids 是数组
                nodes = graph_data.get("nodes", [])
                for i in range(0, len(nodes), batch_size):
                    batch = nodes[i:i+batch_size]
                    for node in batch:
                        try:
                            tx.run("""
                                MERGE (n:Entity {id: $id})
                                ON CREATE SET
                                    n.label = $label,
                                    n.type = $type,
                                    n.description = $description,
                                    n.doc_ids = [$doc_id],
                                    n.created_at = datetime()
                                ON MATCH SET
                                    n.description = CASE
                                        WHEN n.description IS NULL OR n.description = ''
                                        THEN $description
                                        ELSE n.description
                                    END,
                                    n.doc_ids = CASE
                                        WHEN NOT $doc_id IN n.doc_ids
                                        THEN n.doc_ids + $doc_id
                                        ELSE n.doc_ids
                                    END,
                                    n.updated_at = datetime()
                            """,
                                id=node.get("id"),
                                label=node.get("label"),
                                type=node.get("type"),
                                description=node.get("description", ""),
                                doc_id=doc_id
                            )
                            stats["nodes_created"] += 1
                        except Exception as e:
                            print(f"节点创建失败: {e}")
                            stats["failed"] += 1

                # 批量创建关系
                edges = graph_data.get("edges", [])
                for i in range(0, len(edges), batch_size):
                    batch = edges[i:i+batch_size]
                    for edge in batch:
                        try:
                            # 获取中文关系标签
                            chinese_label = edge.get("label", "RELATES")

                            # 转换为 Neo4j 兼容的关系类型
                            rel_type = normalize_relation_type(chinese_label)

                            # 使用动态关系类型（通过字符串拼接，因为 Cypher 不支持参数化关系类型）
                            query = f"""
                                MATCH (s:Entity {{id: $source}})
                                MATCH (t:Entity {{id: $target}})
                                MERGE (s)-[r:{rel_type}]->(t)
                                SET r.label = $label,
                                    r.weight = $weight,
                                    r.doc_id = $doc_id,
                                    r.updated_at = datetime()
                            """

                            tx.run(query,
                                source=edge.get("source"),
                                target=edge.get("target"),
                                label=chinese_label,  # 保存中文标签
                                weight=edge.get("weight", 1),
                                doc_id=doc_id
                            )
                            stats["edges_created"] += 1
                        except Exception as e:
                            print(f"关系创建失败 ({chinese_label}): {e}")
                            stats["failed"] += 1

        # 创建索引（在事务外部，使用单独的 session）
        try:
            with self.driver.session() as index_session:
                index_session.run("CREATE INDEX entity_id_index IF NOT EXISTS FOR (n:Entity) ON (n.id)")
                index_session.run("CREATE INDEX entity_type_index IF NOT EXISTS FOR (n:Entity) ON (n.type)")
        except Exception as e:
            # 索引已存在时会报错，可以忽略
            pass

        return stats

    def query_subgraph(self, entity_id: str, n_hops: int = 1) -> Dict:
        """
        查询实体的 N 跳子图

        Args:
            entity_id: 实体 ID
            n_hops: 跳数

        Returns:
            子图数据
        """
        with self.driver.session() as session:
            result = session.run(f"""
                MATCH path = (start:Entity {{id: $entity_id}})-[*1..{n_hops}]-(connected)
                WITH start, connected, relationships(path) as rels
                RETURN
                    collect(DISTINCT {{
                        id: start.id,
                        label: start.label,
                        type: start.type,
                        description: start.description
                    }}) +
                    collect(DISTINCT {{
                        id: connected.id,
                        label: connected.label,
                        type: connected.type,
                        description: connected.description
                    }}) as nodes,
                    [r in rels | {{
                        source: startNode(r).id,
                        target: endNode(r).id,
                        label: type(r),
                        weight: r.weight
                    }}] as edges
            """, entity_id=entity_id)

            record = result.single()
            if record:
                return {
                    "nodes": record["nodes"],
                    "edges": record["edges"]
                }
            return {"nodes": [], "edges": []}

    def delete_by_doc(self, doc_id: str) -> Dict:
        """
        删除指定文档的所有数据

        Args:
            doc_id: 文档 ID

        Returns:
            删除统计信息
        """
        with self.driver.session() as session:
            # 删除关系
            result_edges = session.run("""
                MATCH ()-[r {doc_id: $doc_id}]->()
                DELETE r
                RETURN count(r) as deleted
            """, doc_id=doc_id)

            edges_deleted = result_edges.single()["deleted"]

            # 从节点的 doc_ids 中移除该文档
            # 如果节点只属于这一个文档，则删除节点
            result_nodes = session.run("""
                MATCH (n:Entity)
                WHERE $doc_id IN n.doc_ids
                WITH n,
                     [id IN n.doc_ids WHERE id <> $doc_id] as new_doc_ids,
                     size([id IN n.doc_ids WHERE id <> $doc_id]) as remaining_count
                FOREACH (ignoreMe IN CASE WHEN remaining_count = 0 THEN [1] ELSE [] END |
                    DELETE n
                )
                FOREACH (ignoreMe IN CASE WHEN remaining_count > 0 THEN [1] ELSE [] END |
                    SET n.doc_ids = new_doc_ids
                )
                RETURN count(n) as processed,
                       sum(CASE WHEN remaining_count = 0 THEN 1 ELSE 0 END) as deleted
            """, doc_id=doc_id)

            result = result_nodes.single()
            nodes_deleted = result["deleted"] if result else 0

            return {
                "nodes_deleted": nodes_deleted,
                "edges_deleted": edges_deleted
            }

    def get_stats(self) -> Dict:
        """
        获取 Neo4j 统计信息

        Returns:
            统计信息
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n:Entity)
                OPTIONAL MATCH ()-[r]->()
                RETURN count(DISTINCT n) as node_count, count(r) as edge_count
            """)

            record = result.single()
            return {
                "total_nodes": record["node_count"],
                "total_edges": record["edge_count"]
            }

    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()


# 单例实例
_neo4j_instance = None


def get_neo4j_storage() -> Optional[Neo4jStorage]:
    """
    获取 Neo4j 存储实例（单例模式）

    Returns:
        Neo4jStorage 实例，如果不可用返回 None
    """
    global _neo4j_instance

    if not NEO4J_AVAILABLE:
        return None

    if _neo4j_instance is None:
        try:
            _neo4j_instance = Neo4jStorage()
        except Exception as e:
            print(f"Neo4j 初始化失败: {e}")
            return None

    return _neo4j_instance


# 命令行测试
if __name__ == "__main__":
    storage = get_neo4j_storage()
    if storage:
        print("Neo4j 连接成功")
        print("统计信息:", storage.get_stats())
    else:
        print("Neo4j 不可用")
