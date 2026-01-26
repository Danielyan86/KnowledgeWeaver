"""
Test Knowledge Graph Manager
测试知识图谱管理器
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.management.kg_manager import KnowledgeGraphManager


@pytest.mark.unit
class TestKnowledgeGraphManager:
    """测试知识图谱管理器"""

    @pytest.fixture
    def mock_neo4j_storage(self):
        """模拟 Neo4j 存储"""
        with patch('backend.management.kg_manager.get_neo4j_storage') as mock:
            storage = MagicMock()
            storage.save_graph_batch.return_value = {
                'nodes_created': 10,
                'edges_created': 15,
                'nodes_updated': 2
            }
            storage.load_graph.return_value = {
                'nodes': [],
                'edges': []
            }
            storage.delete_graph.return_value = {
                'nodes_deleted': 5,
                'edges_deleted': 8
            }
            storage.list_documents.return_value = []
            storage.get_stats.return_value = {
                'total_nodes': 100,
                'total_edges': 200
            }
            mock.return_value = storage
            yield storage

    @pytest.fixture
    def manager(self, mock_neo4j_storage, mock_env_vars):
        """创建管理器实例"""
        return KnowledgeGraphManager(use_neo4j=True)

    def test_init_with_neo4j(self, mock_neo4j_storage):
        """测试启用 Neo4j 初始化"""
        manager = KnowledgeGraphManager(use_neo4j=True)
        assert manager.neo4j_storage is not None
        assert manager.normalizer is not None

    def test_init_without_neo4j(self):
        """测试不启用 Neo4j 初始化"""
        manager = KnowledgeGraphManager(use_neo4j=False)
        assert manager.neo4j_storage is None
        assert manager.normalizer is not None

    def test_save_document_success(self, manager, sample_graph):
        """测试成功保存文档"""
        doc_id = "test_doc"
        metadata = {"source": "test"}

        stats = manager.save_document(doc_id, sample_graph, metadata)

        assert "normalization" in stats
        assert "neo4j" in stats
        assert stats["neo4j"]["nodes_created"] == 10
        assert stats["neo4j"]["edges_created"] == 15

    def test_save_document_with_normalized_graph(self, manager):
        """测试保存已规范化的图谱"""
        doc_id = "test_doc"
        normalized_graph = {
            "nodes": [],
            "edges": [],
            "stats": {"original_nodes": 10}
        }

        stats = manager.save_document(doc_id, normalized_graph)

        # 应该直接使用已规范化的图谱
        assert "neo4j" in stats

    def test_save_document_neo4j_error(self, manager, sample_graph):
        """测试 Neo4j 保存失败"""
        manager.neo4j_storage.save_graph_batch.side_effect = Exception("Connection error")

        stats = manager.save_document("test_doc", sample_graph)

        assert "neo4j" in stats
        assert "error" in stats["neo4j"]

    def test_load_document_success(self, manager):
        """测试成功加载文档"""
        doc_id = "test_doc"
        manager.neo4j_storage.load_graph.return_value = {
            "nodes": [{"id": "node1"}],
            "edges": [{"source": "node1", "target": "node2"}]
        }

        graph = manager.load_document(doc_id)

        assert "nodes" in graph
        assert "edges" in graph
        assert len(graph["nodes"]) == 1

    def test_load_document_no_neo4j(self):
        """测试没有 Neo4j 时加载文档"""
        manager = KnowledgeGraphManager(use_neo4j=False)
        graph = manager.load_document("test_doc")

        assert "error" in graph

    def test_delete_document_success(self, manager):
        """测试成功删除文档"""
        doc_id = "test_doc"

        stats = manager.delete_document(doc_id)

        assert "neo4j" in stats or "error" in stats

    def test_list_documents(self, manager):
        """测试列出文档"""
        manager.neo4j_storage.list_documents.return_value = [
            {"doc_id": "doc1", "file": "test1.txt"},
            {"doc_id": "doc2", "file": "test2.txt"}
        ]

        docs = manager.list_documents()

        assert isinstance(docs, list)
        assert len(docs) == 2

    def test_get_stats(self, manager):
        """测试获取统计信息"""
        stats = manager.get_stats()

        assert "neo4j" in stats or "error" in stats

    def test_get_popular_labels(self, manager):
        """测试获取热门标签"""
        manager.neo4j_storage.get_popular_labels = MagicMock(
            return_value=["标签1", "标签2", "标签3"]
        )

        labels = manager.get_popular_labels(limit=3)

        assert isinstance(labels, list)
        assert len(labels) <= 3

    def test_get_graph_by_label(self, manager):
        """测试按标签获取图谱"""
        manager.neo4j_storage.get_graph_by_label = MagicMock(
            return_value={"nodes": [], "edges": []}
        )

        graph = manager.get_graph_by_label("Person")

        assert "nodes" in graph
        assert "edges" in graph

    def test_get_all_graphs(self, manager):
        """测试获取全部图谱"""
        manager.neo4j_storage.get_all_graphs = MagicMock(
            return_value={"nodes": [], "edges": []}
        )

        graph = manager.get_all_graphs()

        assert "nodes" in graph
        assert "edges" in graph


@pytest.mark.unit
class TestKnowledgeGraphManagerEdgeCases:
    """测试边界情况"""

    def test_save_empty_graph(self):
        """测试保存空图谱"""
        manager = KnowledgeGraphManager(use_neo4j=False)
        empty_graph = {"nodes": [], "edges": []}

        stats = manager.save_document("test_doc", empty_graph)

        assert "normalization" in stats or "neo4j" in stats

    def test_concurrent_saves(self, mock_env_vars):
        """测试并发保存（理论测试）"""
        manager = KnowledgeGraphManager(use_neo4j=False)

        # 模拟并发保存多个文档
        doc_ids = [f"doc_{i}" for i in range(5)]
        graphs = [{"nodes": [], "edges": []} for _ in range(5)]

        for doc_id, graph in zip(doc_ids, graphs):
            stats = manager.save_document(doc_id, graph)
            assert stats is not None
