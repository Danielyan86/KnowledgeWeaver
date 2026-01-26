"""
QA Prompts
问答系统提示词

功能：
- 查询分类 prompt
- 答案生成 prompt (KG/RAG/混合)
"""

from typing import List, Dict
from enum import Enum


class QueryType(Enum):
    """查询类型"""
    FACTUAL = "factual"          # 事实性问题：谁/什么/哪个
    EXPLORATORY = "exploratory"  # 探索性问题：介绍/说明
    ANALYTICAL = "analytical"    # 分析性问题：为什么/如何
    RELATIONAL = "relational"    # 关系性问题：关系/关联


# 查询分类提示词
QUERY_CLASSIFICATION_PROMPT = """你是一个查询分类专家。请分析用户问题，判断其属于以下哪种类型：

1. FACTUAL - 事实性问题
   - 特征：询问具体的人物、事物、时间、地点、数字等
   - 关键词：谁、什么、哪个、哪里、多少、是否
   - 示例："李笑来是谁？"、"定投策略是什么？"

2. EXPLORATORY - 探索性问题
   - 特征：希望了解某个主题的全面介绍或说明
   - 关键词：介绍、说明、描述、概述、讲讲
   - 示例："介绍一下长期主义"、"说说定投的好处"

3. ANALYTICAL - 分析性问题
   - 特征：需要分析原因、过程或方法
   - 关键词：为什么、如何、怎么、怎样、原因
   - 示例："为什么要选择定投？"、"如何实践长期主义？"

4. RELATIONAL - 关系性问题
   - 特征：询问实体之间的关系或关联
   - 关键词：关系、关联、联系、与...有关、之间
   - 示例："李笑来和定投有什么关系？"、"哪些概念与长期主义相关？"

用户问题：{question}

请仅返回一个类型名称（FACTUAL/EXPLORATORY/ANALYTICAL/RELATIONAL），不要有其他内容。"""


# KG 优先的答案生成提示词
KG_ANSWER_PROMPT = """你是一个知识图谱问答助手。基于以下知识图谱信息回答用户问题。

## 相关实体
{entities}

## 相关关系
{relations}

## 用户问题
{question}

## 要求
1. 仅基于提供的知识图谱信息回答
2. 如果信息不足，明确告知用户
3. 答案要简洁、准确
4. 如果涉及多个实体，说明它们之间的关系

请回答："""


# RAG 优先的答案生成提示词
RAG_ANSWER_PROMPT = """你是一个文档问答助手。基于以下文档片段回答用户问题。

## 相关文档片段
{chunks}

## 用户问题
{question}

## 要求
1. 仅基于提供的文档片段回答
2. 如果信息不足，明确告知用户
3. 答案要有条理、详细
4. 可以适当总结和概括

请回答："""


# 混合答案生成提示词
HYBRID_ANSWER_PROMPT = """你是一个智能问答助手。基于以下知识图谱和文档信息回答用户问题。

## 知识图谱信息
### 相关实体
{entities}

### 相关关系
{relations}

## 文档片段
{chunks}

## 用户问题
{question}

## 要求
1. 综合知识图谱的结构化信息和文档的详细内容回答
2. 知识图谱提供了实体和关系的概览，文档提供了详细的上下文
3. 如果两者信息有补充，请整合回答
4. 如果信息不足，明确告知用户
5. 答案要准确、全面、有条理

请回答："""


# 实体提取提示词（从问题中提取实体用于 KG 检索）
ENTITY_EXTRACTION_PROMPT = """从以下问题中提取关键实体/概念名称（人名、书名、概念、策略等）。

问题：{question}

仅返回实体名称列表，用逗号分隔。如果没有明确的实体，返回"无"。

示例：
- 问题："李笑来的投资理念是什么？" -> 李笑来, 投资理念
- 问题："定投策略有什么好处？" -> 定投策略
- 问题："这本书讲了什么？" -> 无

实体列表："""


def get_classification_prompt(question: str) -> str:
    """获取查询分类提示词"""
    return QUERY_CLASSIFICATION_PROMPT.format(question=question)


def get_entity_extraction_prompt(question: str) -> str:
    """获取实体提取提示词"""
    return ENTITY_EXTRACTION_PROMPT.format(question=question)


def format_entities_for_prompt(entities: List[Dict]) -> str:
    """格式化实体信息用于 prompt"""
    if not entities:
        return "无相关实体"

    lines = []
    for entity in entities:
        label = entity.get("label", entity.get("id", ""))
        entity_type = entity.get("type", "Entity")
        description = entity.get("description", "")

        line = f"- **{label}** ({entity_type})"
        if description:
            line += f": {description}"
        lines.append(line)

    return "\n".join(lines)


def format_relations_for_prompt(relations: List[Dict]) -> str:
    """格式化关系信息用于 prompt"""
    if not relations:
        return "无相关关系"

    lines = []
    for rel in relations:
        source = rel.get("source", "")
        target = rel.get("target", "")
        label = rel.get("label", rel.get("relation", ""))
        lines.append(f"- {source} --[{label}]--> {target}")

    return "\n".join(lines)


def format_chunks_for_prompt(chunks: List[Dict]) -> str:
    """格式化文档片段用于 prompt"""
    if not chunks:
        return "无相关文档片段"

    lines = []
    for i, chunk in enumerate(chunks, 1):
        text = chunk.get("text", "")
        score = chunk.get("score", 0)
        lines.append(f"[片段 {i}] (相关度: {score:.2f})\n{text}")

    return "\n\n".join(lines)


def get_kg_answer_prompt(
    question: str,
    entities: List[Dict],
    relations: List[Dict]
) -> str:
    """获取 KG 优先的答案生成提示词"""
    return KG_ANSWER_PROMPT.format(
        question=question,
        entities=format_entities_for_prompt(entities),
        relations=format_relations_for_prompt(relations)
    )


def get_rag_answer_prompt(
    question: str,
    chunks: List[Dict]
) -> str:
    """获取 RAG 优先的答案生成提示词"""
    return RAG_ANSWER_PROMPT.format(
        question=question,
        chunks=format_chunks_for_prompt(chunks)
    )


def get_hybrid_answer_prompt(
    question: str,
    entities: List[Dict],
    relations: List[Dict],
    chunks: List[Dict]
) -> str:
    """获取混合答案生成提示词"""
    return HYBRID_ANSWER_PROMPT.format(
        question=question,
        entities=format_entities_for_prompt(entities),
        relations=format_relations_for_prompt(relations),
        chunks=format_chunks_for_prompt(chunks)
    )


# 根据查询类型获取推荐的检索策略
RETRIEVAL_STRATEGY = {
    QueryType.FACTUAL: "kg_first",      # KG 优先
    QueryType.EXPLORATORY: "rag_first", # RAG 优先
    QueryType.ANALYTICAL: "hybrid",     # 混合
    QueryType.RELATIONAL: "kg_only"     # 仅 KG
}


def get_retrieval_strategy(query_type: QueryType) -> str:
    """根据查询类型获取检索策略"""
    return RETRIEVAL_STRATEGY.get(query_type, "hybrid")
