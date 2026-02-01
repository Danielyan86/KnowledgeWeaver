"""
Test Embedding Service
测试嵌入服务
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.core.embeddings.service import EmbeddingService


@pytest.mark.unit
class TestEmbeddingService:
    """测试嵌入服务"""

    @pytest.fixture
    def mock_openai_client(self):
        """模拟 OpenAI 客户端"""
        # Patch openai.OpenAI 而不是 backend.core.embeddings.service.OpenAI
        with patch('openai.OpenAI') as mock_client:
            # 模拟 embeddings.create 响应（支持批量）
            def mock_create(model, input):
                # 如果是单个文本，返回一个嵌入
                if isinstance(input, str):
                    return MagicMock(data=[MagicMock(embedding=[0.1, 0.2, 0.3])])
                # 如果是文本列表，返回多个嵌入
                else:
                    return MagicMock(data=[
                        MagicMock(embedding=[0.1 * (i+1), 0.2 * (i+1), 0.3 * (i+1)])
                        for i in range(len(input))
                    ])

            mock_client.return_value.embeddings.create.side_effect = mock_create
            yield mock_client

    @pytest.fixture
    def service(self, mock_openai_client, mock_env_vars):
        """创建嵌入服务实例"""
        return EmbeddingService()

    def test_embed_text_success(self, service):
        """测试成功生成单个文本嵌入"""
        text = "这是一个测试文本"
        embedding = service.embed_text(text)

        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)

    def test_embed_text_empty(self, service):
        """测试空文本"""
        assert service.embed_text("") == []
        assert service.embed_text("  ") == []

    def test_embed_text_caching(self, service):
        """测试缓存机制"""
        text = "测试文本"

        # 第一次调用
        embedding1 = service.embed_text(text)

        # 第二次调用应该使用缓存
        embedding2 = service.embed_text(text)

        assert embedding1 == embedding2
        # OpenAI API 应该只被调用一次
        assert service.client.embeddings.create.call_count == 1

    def test_embed_text_error_handling(self, service):
        """测试错误处理"""
        service.client.embeddings.create.side_effect = Exception("API Error")

        text = "测试文本"
        embedding = service.embed_text(text)

        assert embedding == []

    def test_embed_texts_success(self, service, sample_chunks):
        """测试批量生成嵌入"""
        embeddings = service.embed_texts(sample_chunks)

        assert isinstance(embeddings, list)
        assert len(embeddings) == len(sample_chunks)
        assert all(isinstance(emb, list) for emb in embeddings)

    def test_embed_texts_empty_list(self, service):
        """测试空列表"""
        assert service.embed_texts([]) == []

    def test_embed_texts_filters_empty(self, service):
        """测试过滤空文本"""
        texts = ["文本1", "", "  ", "文本2"]
        embeddings = service.embed_texts(texts)

        # 应该生成嵌入的文本数量
        assert len([e for e in embeddings if e]) >= 2

    def test_cache_key_generation(self, service):
        """测试缓存键生成"""
        text = "测试文本"
        key1 = service._get_cache_key(text)
        key2 = service._get_cache_key(text)

        assert key1 == key2
        assert isinstance(key1, str)
        assert len(key1) == 32  # MD5 hash length


@pytest.mark.integration
class TestEmbeddingServiceIntegration:
    """集成测试（需要真实 API 密钥）"""

    @pytest.mark.skip(reason="需要真实 API 密钥")
    def test_real_api_call(self):
        """测试真实 API 调用"""
        service = EmbeddingService()
        text = "李笑来在《让时间陪你慢慢变富》中主张定投策略。"
        embedding = service.embed_text(text)

        assert len(embedding) > 0
        assert len(embedding) == 1536  # OpenAI ada-002 维度
