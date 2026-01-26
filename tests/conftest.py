"""
Pytest Configuration and Fixtures
pytest 配置和共享 fixture
"""

import os
import sys
from pathlib import Path
from typing import Dict, List

import pytest
from fastapi.testclient import TestClient


# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_entities() -> List[Dict]:
    """示例实体数据"""
    return [
        {"name": "李笑来", "type": "Person"},
        {"name": "让时间陪你慢慢变富", "type": "Book"},
        {"name": "定投", "type": "Strategy"},
        {"name": "普通人", "type": "Group"},
        {"name": "标普500指数基金", "type": "Concept"}
    ]


@pytest.fixture
def sample_relations() -> List[Dict]:
    """示例关系数据"""
    return [
        {"source": "李笑来", "target": "让时间陪你慢慢变富", "relation": "著作"},
        {"source": "让时间陪你慢慢变富", "target": "定投", "relation": "主张"},
        {"source": "定投", "target": "普通人", "relation": "适用于"},
        {"source": "定投", "target": "标普500指数基金", "relation": "推荐"}
    ]


@pytest.fixture
def sample_graph() -> Dict:
    """示例知识图谱数据"""
    return {
        "nodes": [
            {"id": "李笑来", "label": "李笑来", "type": "Person", "description": "投资者和作家", "degree": 2},
            {"id": "让时间陪你慢慢变富", "label": "让时间陪你慢慢变富", "type": "Book", "description": "投资书籍", "degree": 2},
            {"id": "定投", "label": "定投", "type": "Strategy", "description": "投资策略", "degree": 3},
            {"id": "普通人", "label": "普通人", "type": "Group", "description": "大众群体", "degree": 1},
        ],
        "edges": [
            {"source": "李笑来", "target": "让时间陪你慢慢变富", "label": "著作", "weight": 1},
            {"source": "让时间陪你慢慢变富", "target": "定投", "label": "主张", "weight": 1},
            {"source": "定投", "target": "普通人", "label": "适用于", "weight": 1},
        ]
    }


@pytest.fixture
def sample_chunks() -> List[str]:
    """示例文本块"""
    return [
        "李笑来是一位投资者和作家。",
        "他在《让时间陪你慢慢变富》中主张定投策略。",
        "定投策略适合普通人进行长期投资。",
        "标普500指数基金是定投的推荐标的之一。"
    ]


@pytest.fixture
def mock_env_vars(monkeypatch):
    """模拟环境变量"""
    monkeypatch.setenv("USE_NEO4J", "false")
    monkeypatch.setenv("LLM_BINDING_HOST", "https://api.example.com/v1")
    monkeypatch.setenv("LLM_BINDING_API_KEY", "test-key")
    monkeypatch.setenv("EMBEDDING_MODEL", "text-embedding-ada-002")
    monkeypatch.setenv("PORT", "9621")
    monkeypatch.setenv("HOST", "127.0.0.1")


@pytest.fixture
def test_data_dir(tmp_path) -> Path:
    """临时测试数据目录"""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()

    # 创建子目录
    (data_dir / "storage" / "vector_db").mkdir(parents=True)
    (data_dir / "checkpoints").mkdir()
    (data_dir / "progress").mkdir()
    (data_dir / "inputs" / "__enqueued__").mkdir(parents=True)

    return data_dir


@pytest.fixture
def sample_text_file(test_data_dir) -> Path:
    """创建示例文本文件"""
    file_path = test_data_dir / "inputs" / "__enqueued__" / "test.txt"
    content = """
    李笑来在《让时间陪你慢慢变富》中主张定投策略。
    定投策略适合普通人进行长期投资。
    他推荐标普500指数基金作为定投标的。
    长期主义是投资的核心理念。
    """
    file_path.write_text(content, encoding='utf-8')
    return file_path


@pytest.fixture
def api_client(mock_env_vars):
    """FastAPI 测试客户端"""
    # 延迟导入以确保环境变量已设置
    from backend.server import app
    return TestClient(app)


# Pytest 配置
def pytest_configure(config):
    """Pytest 配置"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
