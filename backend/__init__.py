"""
Backend Package
后端包 - KnowledgeWeaver

提供向后兼容的导入路径
"""

# Core imports
from .core.config import *
from .core.storage import get_neo4j_storage, get_vector_store, Neo4jStorage, VectorStore
from .core.embeddings import get_embedding_service, EmbeddingService

# Extraction imports
from .extraction import (
    KnowledgeGraphExtractor,
    AsyncKnowledgeGraphExtractor,
    KnowledgeGraphNormalizer,
    EntityFilter
)

# Retrieval imports
from .retrieval import (
    get_retriever,
    HybridRetriever,
    get_qa_engine,
    QAEngine
)
from .retrieval import prompts

# Management imports
from .management import (
    get_kg_manager,
    KnowledgeGraphManager,
    get_progress_tracker,
    ProgressTracker
)

__all__ = [
    # Core
    "get_neo4j_storage",
    "Neo4jStorage",
    "get_vector_store",
    "VectorStore",
    "get_embedding_service",
    "EmbeddingService",
    # Extraction
    "KnowledgeGraphExtractor",
    "AsyncKnowledgeGraphExtractor",
    "KnowledgeGraphNormalizer",
    "EntityFilter",
    # Retrieval
    "get_retriever",
    "HybridRetriever",
    "get_qa_engine",
    "QAEngine",
    "prompts",
    # Management
    "get_kg_manager",
    "KnowledgeGraphManager",
    "get_progress_tracker",
    "ProgressTracker"
]
