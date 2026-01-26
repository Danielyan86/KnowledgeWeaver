"""
Vector Store
向量存储模块

功能：
- ChromaDB 封装
- 文档 chunk 存储和检索
- 实体 embedding 存储
"""

import os
from typing import List, Dict, Optional, Any
from pathlib import Path

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

from backend.core.embeddings.service import get_embedding_service


load_dotenv()


class VectorStore:
    """向量存储"""

    CHUNKS_COLLECTION = "document_chunks"
    ENTITIES_COLLECTION = "kg_entities"

    def __init__(self, persist_dir: Optional[str] = None):
        """
        初始化向量存储

        Args:
            persist_dir: 持久化目录路径
        """
        if persist_dir is None:
            persist_dir = os.getenv('CHROMA_PERSIST_DIR', './data/storage/vector_db')

        # 确保目录存在
        Path(persist_dir).mkdir(parents=True, exist_ok=True)

        # 初始化 ChromaDB
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )

        self.embedding_service = get_embedding_service()

        # 获取或创建集合
        self._chunks_collection = self.client.get_or_create_collection(
            name=self.CHUNKS_COLLECTION,
            metadata={"description": "Document text chunks for RAG"}
        )
        self._entities_collection = self.client.get_or_create_collection(
            name=self.ENTITIES_COLLECTION,
            metadata={"description": "Knowledge graph entities"}
        )

    # ==================== Chunks 操作 ====================

    def add_chunks(
        self,
        chunks: List[str],
        doc_id: str,
        metadata_list: Optional[List[Dict]] = None
    ) -> List[str]:
        """
        添加文档 chunks

        Args:
            chunks: 文本块列表
            doc_id: 文档 ID
            metadata_list: 每个 chunk 的元数据

        Returns:
            chunk ID 列表
        """
        if not chunks:
            return []

        # 生成 embeddings
        embeddings = self.embedding_service.embed_texts(chunks)

        # 生成 IDs
        chunk_ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]

        # 准备元数据
        metadatas = []
        for i, chunk in enumerate(chunks):
            meta = {
                "doc_id": doc_id,
                "chunk_index": i,
                "text_length": len(chunk)
            }
            if metadata_list and i < len(metadata_list):
                meta.update(metadata_list[i])
            metadatas.append(meta)

        # 过滤掉空 embedding 的 chunks
        valid_data = [
            (chunk_ids[i], chunks[i], embeddings[i], metadatas[i])
            for i in range(len(chunks))
            if embeddings[i]
        ]

        if not valid_data:
            return []

        ids, documents, embs, metas = zip(*valid_data)

        self._chunks_collection.add(
            ids=list(ids),
            documents=list(documents),
            embeddings=list(embs),
            metadatas=list(metas)
        )

        return list(ids)

    def search_chunks(
        self,
        query: str,
        top_k: int = 5,
        doc_id: Optional[str] = None
    ) -> List[Dict]:
        """
        搜索相似 chunks

        Args:
            query: 查询文本
            top_k: 返回数量
            doc_id: 限定文档 ID（可选）

        Returns:
            搜索结果列表
        """
        query_embedding = self.embedding_service.embed_text(query)
        if not query_embedding:
            return []

        where_filter = {"doc_id": doc_id} if doc_id else None

        results = self._chunks_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        # 整理结果
        items = []
        if results and results.get("ids"):
            ids = results["ids"][0]
            documents = results["documents"][0] if results.get("documents") else []
            metadatas = results["metadatas"][0] if results.get("metadatas") else []
            distances = results["distances"][0] if results.get("distances") else []

            for i, chunk_id in enumerate(ids):
                items.append({
                    "id": chunk_id,
                    "text": documents[i] if i < len(documents) else "",
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "distance": distances[i] if i < len(distances) else 0,
                    "score": 1 - (distances[i] if i < len(distances) else 0)  # 转换为相似度
                })

        return items

    def delete_chunks_by_doc(self, doc_id: str) -> int:
        """
        删除指定文档的所有 chunks

        Args:
            doc_id: 文档 ID

        Returns:
            删除的 chunk 数量
        """
        # 先查询该文档的所有 chunks
        results = self._chunks_collection.get(
            where={"doc_id": doc_id},
            include=[]
        )

        if not results or not results.get("ids"):
            return 0

        chunk_ids = results["ids"]
        self._chunks_collection.delete(ids=chunk_ids)

        return len(chunk_ids)

    def get_chunks_count(self, doc_id: Optional[str] = None) -> int:
        """获取 chunk 数量"""
        if doc_id:
            results = self._chunks_collection.get(
                where={"doc_id": doc_id},
                include=[]
            )
            return len(results["ids"]) if results.get("ids") else 0
        return self._chunks_collection.count()

    # ==================== Entities 操作 ====================

    def add_entities(
        self,
        entities: List[Dict],
        doc_id: str
    ) -> List[str]:
        """
        添加知识图谱实体

        Args:
            entities: 实体列表，每个包含 id, label, type, description
            doc_id: 文档 ID

        Returns:
            实体 ID 列表
        """
        if not entities:
            return []

        # 构建文本用于 embedding（名称 + 描述）
        texts = []
        for entity in entities:
            text = entity.get("label", entity.get("id", ""))
            desc = entity.get("description", "")
            if desc:
                text = f"{text}: {desc}"
            texts.append(text)

        # 生成 embeddings
        embeddings = self.embedding_service.embed_texts(texts)

        # 生成 IDs（使用 doc_id + entity_id 避免冲突）
        entity_ids = [f"{doc_id}_entity_{entity.get('id', str(i))}" for i, entity in enumerate(entities)]

        # 准备元数据
        metadatas = []
        for entity in entities:
            metadatas.append({
                "doc_id": doc_id,
                "entity_id": entity.get("id", ""),
                "label": entity.get("label", ""),
                "type": entity.get("type", "Entity"),
                "description": entity.get("description", ""),
                "degree": entity.get("degree", 0)
            })

        # 准备文档（用于存储原始文本）
        documents = texts

        # 过滤掉空 embedding 的实体
        valid_data = [
            (entity_ids[i], documents[i], embeddings[i], metadatas[i])
            for i in range(len(entities))
            if embeddings[i]
        ]

        if not valid_data:
            return []

        ids, docs, embs, metas = zip(*valid_data)

        self._entities_collection.add(
            ids=list(ids),
            documents=list(docs),
            embeddings=list(embs),
            metadatas=list(metas)
        )

        return list(ids)

    def search_entities(
        self,
        query: str,
        top_k: int = 5,
        entity_type: Optional[str] = None
    ) -> List[Dict]:
        """
        搜索相似实体

        Args:
            query: 查询文本
            top_k: 返回数量
            entity_type: 限定实体类型（可选）

        Returns:
            搜索结果列表
        """
        query_embedding = self.embedding_service.embed_text(query)
        if not query_embedding:
            return []

        where_filter = {"type": entity_type} if entity_type else None

        results = self._entities_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        # 整理结果
        items = []
        if results and results.get("ids"):
            ids = results["ids"][0]
            metadatas = results["metadatas"][0] if results.get("metadatas") else []
            distances = results["distances"][0] if results.get("distances") else []

            for i, store_id in enumerate(ids):
                meta = metadatas[i] if i < len(metadatas) else {}
                items.append({
                    "id": meta.get("entity_id", ""),
                    "label": meta.get("label", ""),
                    "type": meta.get("type", "Entity"),
                    "description": meta.get("description", ""),
                    "degree": meta.get("degree", 0),
                    "doc_id": meta.get("doc_id", ""),
                    "distance": distances[i] if i < len(distances) else 0,
                    "score": 1 - (distances[i] if i < len(distances) else 0)
                })

        return items

    def delete_entities_by_doc(self, doc_id: str) -> int:
        """
        删除指定文档的所有实体

        Args:
            doc_id: 文档 ID

        Returns:
            删除的实体数量
        """
        results = self._entities_collection.get(
            where={"doc_id": doc_id},
            include=[]
        )

        if not results or not results.get("ids"):
            return 0

        entity_ids = results["ids"]
        self._entities_collection.delete(ids=entity_ids)

        return len(entity_ids)

    def get_entities_count(self, doc_id: Optional[str] = None) -> int:
        """获取实体数量"""
        if doc_id:
            results = self._entities_collection.get(
                where={"doc_id": doc_id},
                include=[]
            )
            return len(results["ids"]) if results.get("ids") else 0
        return self._entities_collection.count()

    # ==================== 通用操作 ====================

    def delete_by_doc(self, doc_id: str) -> Dict[str, int]:
        """
        删除指定文档的所有数据

        Args:
            doc_id: 文档 ID

        Returns:
            删除统计
        """
        chunks_deleted = self.delete_chunks_by_doc(doc_id)
        entities_deleted = self.delete_entities_by_doc(doc_id)

        return {
            "chunks_deleted": chunks_deleted,
            "entities_deleted": entities_deleted
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计"""
        return {
            "total_chunks": self._chunks_collection.count(),
            "total_entities": self._entities_collection.count()
        }

    def clear_all(self):
        """清空所有数据"""
        # 删除并重新创建集合
        self.client.delete_collection(self.CHUNKS_COLLECTION)
        self.client.delete_collection(self.ENTITIES_COLLECTION)

        self._chunks_collection = self.client.get_or_create_collection(
            name=self.CHUNKS_COLLECTION,
            metadata={"description": "Document text chunks for RAG"}
        )
        self._entities_collection = self.client.get_or_create_collection(
            name=self.ENTITIES_COLLECTION,
            metadata={"description": "Knowledge graph entities"}
        )


# 单例
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """获取 VectorStore 实例（单例）"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


# 命令行测试
if __name__ == "__main__":
    store = get_vector_store()

    print(f"初始统计: {store.get_stats()}")

    # 测试添加 chunks
    test_chunks = [
        "李笑来在《让时间陪你慢慢变富》中主张定投策略。",
        "定投是最适合普通人的投资方式，推荐标普500指数基金。",
        "长期主义是这本书的核心理念，强调时间复利的重要性。"
    ]
    chunk_ids = store.add_chunks(test_chunks, "test_doc_1")
    print(f"添加 chunks: {chunk_ids}")

    # 测试添加实体
    test_entities = [
        {"id": "李笑来", "label": "李笑来", "type": "Person", "description": "投资人、作家"},
        {"id": "定投策略", "label": "定投策略", "type": "Strategy", "description": "定期定额投资策略"},
        {"id": "长期主义", "label": "长期主义", "type": "Concept", "description": "长期持有的投资理念"}
    ]
    entity_ids = store.add_entities(test_entities, "test_doc_1")
    print(f"添加实体: {entity_ids}")

    print(f"添加后统计: {store.get_stats()}")

    # 测试搜索
    print("\n搜索 chunks '投资理念':")
    results = store.search_chunks("投资理念", top_k=2)
    for r in results:
        print(f"  - {r['text'][:50]}... (score: {r['score']:.3f})")

    print("\n搜索实体 '投资':")
    results = store.search_entities("投资", top_k=2)
    for r in results:
        print(f"  - {r['label']} ({r['type']}): {r['description']} (score: {r['score']:.3f})")

    # 清理测试数据
    deleted = store.delete_by_doc("test_doc_1")
    print(f"\n清理测试数据: {deleted}")
    print(f"最终统计: {store.get_stats()}")
