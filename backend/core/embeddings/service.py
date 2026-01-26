"""
Embedding Service
向量嵌入服务

功能：
- 调用 OpenAI 兼容 API 生成 embedding
- 批量处理 + 缓存
"""

import os
import hashlib
from typing import List, Dict, Optional
from functools import lru_cache

from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()


class EmbeddingService:
    """Embedding 服务"""

    def __init__(self):
        """初始化 Embedding 服务"""
        api_base = os.getenv('LLM_BINDING_HOST', 'https://space.ai-builders.com/backend/v1')
        api_key = os.getenv('LLM_BINDING_API_KEY', '')
        self.model = os.getenv('EMBEDDING_MODEL', 'text-embedding-ada-002')

        self.client = OpenAI(
            base_url=api_base,
            api_key=api_key
        )

        # 内存缓存
        self._cache: Dict[str, List[float]] = {}

    def _get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def embed_text(self, text: str) -> List[float]:
        """
        生成单个文本的 embedding

        Args:
            text: 待嵌入的文本

        Returns:
            embedding 向量
        """
        if not text or not text.strip():
            return []

        text = text.strip()

        # 检查缓存
        cache_key = self._get_cache_key(text)
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            embedding = response.data[0].embedding

            # 存入缓存
            self._cache[cache_key] = embedding

            return embedding
        except Exception as e:
            print(f"Embedding 生成失败: {e}")
            return []

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成 embedding

        Args:
            texts: 待嵌入的文本列表

        Returns:
            embedding 向量列表
        """
        if not texts:
            return []

        # 过滤空文本并去重
        valid_texts = []
        text_indices = []  # 记录原始索引
        cached_results = {}

        for i, text in enumerate(texts):
            if not text or not text.strip():
                continue

            text = text.strip()
            cache_key = self._get_cache_key(text)

            if cache_key in self._cache:
                cached_results[i] = self._cache[cache_key]
            else:
                valid_texts.append(text)
                text_indices.append(i)

        # 批量请求未缓存的文本
        new_embeddings = {}
        if valid_texts:
            try:
                # 分批处理，每批最多100个
                batch_size = 100
                for batch_start in range(0, len(valid_texts), batch_size):
                    batch_end = min(batch_start + batch_size, len(valid_texts))
                    batch_texts = valid_texts[batch_start:batch_end]
                    batch_indices = text_indices[batch_start:batch_end]

                    response = self.client.embeddings.create(
                        model=self.model,
                        input=batch_texts
                    )

                    for j, emb_data in enumerate(response.data):
                        original_idx = batch_indices[j]
                        embedding = emb_data.embedding
                        new_embeddings[original_idx] = embedding

                        # 存入缓存
                        cache_key = self._get_cache_key(batch_texts[j])
                        self._cache[cache_key] = embedding

            except Exception as e:
                print(f"批量 Embedding 生成失败: {e}")

        # 组合结果
        results = []
        for i in range(len(texts)):
            if i in cached_results:
                results.append(cached_results[i])
            elif i in new_embeddings:
                results.append(new_embeddings[i])
            else:
                results.append([])

        return results

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()

    def get_cache_size(self) -> int:
        """获取缓存大小"""
        return len(self._cache)


# 单例
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """获取 Embedding 服务实例（单例）"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


# 便捷函数
def embed_text(text: str) -> List[float]:
    """生成单个文本的 embedding"""
    return get_embedding_service().embed_text(text)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """批量生成 embedding"""
    return get_embedding_service().embed_texts(texts)


# 命令行测试
if __name__ == "__main__":
    service = get_embedding_service()

    # 测试单个文本
    test_text = "李笑来是一位投资人"
    embedding = service.embed_text(test_text)
    print(f"单文本 embedding 维度: {len(embedding)}")

    # 测试批量
    test_texts = [
        "李笑来的投资理念",
        "定投策略是什么",
        "长期主义的价值"
    ]
    embeddings = service.embed_texts(test_texts)
    print(f"批量 embedding 数量: {len(embeddings)}")
    print(f"缓存大小: {service.get_cache_size()}")
