"""
Test FastAPI Endpoints
测试 FastAPI 端点
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json


@pytest.mark.unit
class TestHealthEndpoint:
    """测试健康检查端点"""

    def test_health_check(self, api_client):
        """测试健康检查"""
        response = api_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


@pytest.mark.unit
class TestGraphEndpoints:
    """测试图谱相关端点"""

    @patch('backend.server.kg_manager')
    def test_get_popular_labels(self, mock_kg_manager, api_client):
        """测试获取热门标签"""
        mock_kg_manager.get_popular_labels.return_value = ["Person", "Book", "Concept"]

        response = api_client.get("/graph/label/popular?limit=3")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 3

    @patch('backend.server.kg_manager')
    def test_get_graphs_all(self, mock_kg_manager, api_client):
        """测试获取全部图谱"""
        mock_kg_manager.get_all_graphs.return_value = {
            "nodes": [{"id": "node1"}],
            "edges": [{"source": "node1", "target": "node2"}]
        }

        response = api_client.get("/graphs")

        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data

    @patch('backend.server.kg_manager')
    def test_get_graphs_by_label(self, mock_kg_manager, api_client):
        """测试按标签获取图谱"""
        mock_kg_manager.get_graph_by_label.return_value = {
            "nodes": [{"id": "person1", "type": "Person"}],
            "edges": []
        }

        response = api_client.get("/graphs?label=Person")

        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data


@pytest.mark.unit
class TestDocumentEndpoints:
    """测试文档相关端点"""

    @patch('backend.server.kg_manager')
    def test_list_documents(self, mock_kg_manager, api_client):
        """测试列出文档"""
        mock_kg_manager.list_documents.return_value = [
            {
                "doc_id": "doc1",
                "file": "test.txt",
                "node_count": 10,
                "edge_count": 15,
                "updated_at": "2026-01-26T00:00:00"
            }
        ]

        response = api_client.get("/documents")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["doc_id"] == "doc1"

    @patch('backend.server.kg_manager')
    def test_get_document_graph(self, mock_kg_manager, api_client):
        """测试获取文档图谱"""
        mock_kg_manager.load_document.return_value = {
            "nodes": [{"id": "node1"}],
            "edges": []
        }

        response = api_client.get("/documents/test_doc")

        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data

    @patch('backend.server.kg_manager')
    def test_get_document_not_found(self, mock_kg_manager, api_client):
        """测试获取不存在的文档"""
        mock_kg_manager.load_document.return_value = {"nodes": []}

        response = api_client.get("/documents/nonexistent")

        assert response.status_code == 404

    @patch('backend.server.kg_manager')
    @patch('backend.server.vector_store')
    def test_delete_document(self, mock_vector_store, mock_kg_manager, api_client):
        """测试删除文档"""
        mock_kg_manager.delete_document.return_value = {
            "neo4j": {"nodes_deleted": 5, "edges_deleted": 8}
        }
        mock_vector_store.delete_by_doc.return_value = {
            "chunks_deleted": 10,
            "entities_deleted": 5
        }

        response = api_client.delete("/documents/test_doc")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "neo4j" in data
        assert "deleted_chunks" in data


@pytest.mark.unit
class TestStatsEndpoint:
    """测试统计端点"""

    @patch('backend.server.kg_manager')
    def test_get_stats(self, mock_kg_manager, api_client):
        """测试获取统计信息"""
        mock_kg_manager.get_stats.return_value = {
            "neo4j": {
                "total_nodes": 100,
                "total_edges": 200
            }
        }
        mock_kg_manager.list_documents.return_value = [
            {"doc_id": "doc1"},
            {"doc_id": "doc2"}
        ]

        response = api_client.get("/stats")

        assert response.status_code == 200
        data = response.json()
        assert "document_count" in data
        assert "total_nodes" in data
        assert "total_edges" in data
        assert data["document_count"] == 2


@pytest.mark.unit
class TestQAEndpoints:
    """测试问答相关端点"""

    @patch('backend.server.qa_engine')
    @patch('backend.core.observability.get_tracer')
    def test_ask_question(self, mock_tracer, mock_qa_engine, api_client):
        """测试问答接口"""
        mock_response = MagicMock()
        mock_response.answer = "这是答案"
        mock_response.sources = {"kg": {}, "rag": {}}
        mock_response.query_type = "factual"
        mock_response.strategy = "hybrid"

        mock_qa_engine.ask.return_value = mock_response
        mock_tracer.return_value.flush = MagicMock()

        payload = {
            "question": "什么是定投？",
            "mode": "auto",
            "n_hops": 1,
            "top_k": 5
        }

        response = api_client.post("/qa", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "strategy" in data

    @patch('backend.server.qa_engine')
    def test_semantic_search(self, mock_qa_engine, api_client):
        """测试语义搜索"""
        mock_qa_engine.search.return_value = {
            "query": "定投策略",
            "chunks": [],
            "entities": []
        }

        payload = {
            "query": "定投策略",
            "search_type": "all",
            "top_k": 10
        }

        response = api_client.post("/search", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "chunks" in data
        assert "entities" in data

    @patch('backend.server.qa_engine')
    def test_get_entity_context(self, mock_qa_engine, api_client):
        """测试获取实体上下文"""
        mock_qa_engine.get_entity_detail.return_value = {
            "entity": {"id": "定投", "type": "Strategy"},
            "related_entities": [],
            "relations": [],
            "chunks": [],
            "summary": "定投是一种投资策略"
        }

        response = api_client.get("/entities/定投/context")

        assert response.status_code == 200
        data = response.json()
        assert "entity" in data
        assert "related_entities" in data
        assert "relations" in data


@pytest.mark.unit
class TestUploadEndpoints:
    """测试文档上传端点"""

    @patch('backend.server.process_document')
    def test_upload_document_txt(self, mock_process, api_client, tmp_path):
        """测试上传 txt 文档"""
        # 创建测试文件
        test_file = tmp_path / "test.txt"
        test_file.write_text("测试内容", encoding='utf-8')

        with open(test_file, 'rb') as f:
            response = api_client.post(
                "/documents/upload",
                files={"file": ("test.txt", f, "text/plain")}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "doc_id" in data

    def test_upload_document_invalid_format(self, api_client, tmp_path):
        """测试上传不支持的文件格式"""
        test_file = tmp_path / "test.doc"
        test_file.write_text("测试内容")

        with open(test_file, 'rb') as f:
            response = api_client.post(
                "/documents/upload",
                files={"file": ("test.doc", f, "application/msword")}
            )

        assert response.status_code == 400


@pytest.mark.integration
class TestAPIIntegration:
    """API 集成测试"""

    @pytest.mark.skip(reason="需要完整环境")
    def test_full_workflow(self, api_client, sample_text_file):
        """测试完整工作流程"""
        # 1. 上传文档
        with open(sample_text_file, 'rb') as f:
            response = api_client.post(
                "/documents/upload-async",
                files={"file": ("test.txt", f, "text/plain")}
            )
        assert response.status_code == 200
        doc_id = response.json()["doc_id"]

        # 2. 查询进度（需要等待处理）
        # response = api_client.get(f"/documents/progress/{doc_id}")
        # assert response.status_code == 200

        # 3. 获取文档图谱
        # response = api_client.get(f"/documents/{doc_id}")
        # assert response.status_code == 200

        # 4. 问答
        # response = api_client.post("/qa", json={"question": "测试问题"})
        # assert response.status_code == 200
