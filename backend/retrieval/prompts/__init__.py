"""
Prompts Package
提示词包

包含：
- extraction_prompts: 知识图谱提取提示词
- qa_prompts: 问答系统提示词
"""

from .extraction_prompts import (
    get_extraction_prompt,
    EXTRACTION_PROMPT,
    STANDARD_RELATIONS,
    NODE_TYPES
)

from .qa_prompts import (
    QueryType,
    get_classification_prompt,
    get_entity_extraction_prompt,
    get_kg_answer_prompt,
    get_rag_answer_prompt,
    get_hybrid_answer_prompt,
    get_retrieval_strategy,
    format_entities_for_prompt,
    format_relations_for_prompt,
    format_chunks_for_prompt
)

__all__ = [
    # Extraction prompts
    "get_extraction_prompt",
    "EXTRACTION_PROMPT",
    "STANDARD_RELATIONS",
    "NODE_TYPES",
    # QA prompts
    "QueryType",
    "get_classification_prompt",
    "get_entity_extraction_prompt",
    "get_kg_answer_prompt",
    "get_rag_answer_prompt",
    "get_hybrid_answer_prompt",
    "get_retrieval_strategy",
    "format_entities_for_prompt",
    "format_relations_for_prompt",
    "format_chunks_for_prompt"
]
