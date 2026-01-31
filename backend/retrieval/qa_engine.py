"""
QA Engine
问答引擎

功能：
- 编排检索流程
- 构建上下文
- LLM 生成答案
- Session 追踪
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass

from openai import OpenAI
from dotenv import load_dotenv
from opentelemetry import trace

from .hybrid_retriever import get_retriever, HybridRetriever
from .prompts.qa_prompts import (
    get_kg_answer_prompt,
    get_rag_answer_prompt,
    get_hybrid_answer_prompt
)
from ..core.observability import get_tracer
from ..core.phoenix_observability import get_phoenix_tracer


load_dotenv()


@dataclass
class QAResponse:
    """问答响应"""
    answer: str
    sources: Dict
    query_type: Optional[str]
    strategy: str
    entities: List[Dict]
    relations: List[Dict]
    chunks: List[Dict]


class QAEngine:
    """问答引擎"""

    def __init__(self):
        """初始化问答引擎"""
        self.retriever = get_retriever()

        # LLM 客户端
        api_base = os.getenv('LLM_BINDING_HOST', 'https://space.ai-builders.com/backend/v1')
        api_key = os.getenv('LLM_BINDING_API_KEY', '')
        self.model = os.getenv('LLM_MODEL', 'deepseek')

        # 创建 OpenAI 客户端
        client = OpenAI(
            base_url=api_base,
            api_key=api_key
        )

        # 使用 Langfuse wrapper 包装客户端（自动追踪所有 LLM 调用）
        tracer = get_tracer()
        self.client = tracer.wrap_openai(client)
        self.observe = tracer.observe  # 获取 observe 装饰器

    def _generate_answer(self, prompt: str) -> str:
        """
        调用 LLM 生成答案

        注意：LLM 调用会被 Langfuse OpenAI wrapper 自动追踪

        Args:
            prompt: 完整的提示词

        Returns:
            生成的答案
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的知识问答助手，基于提供的信息准确、简洁地回答问题。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"生成答案时出错: {e}"

    def _build_sources(
        self,
        entities: List[Dict],
        relations: List[Dict],
        chunks: List[Dict]
    ) -> Dict:
        """
        构建来源信息

        Args:
            entities: 实体列表
            relations: 关系列表
            chunks: 文档片段列表

        Returns:
            来源信息字典
        """
        sources = {
            "kg": {
                "entities": [],
                "relations": []
            },
            "rag": {
                "chunks": []
            }
        }

        # KG 来源
        for entity in entities[:5]:  # 限制数量
            sources["kg"]["entities"].append({
                "label": entity.get("label", entity.get("id", "")),
                "type": entity.get("type", "Entity"),
                "description": entity.get("description", "")[:100]
            })

        for rel in relations[:10]:
            sources["kg"]["relations"].append({
                "source": rel.get("source", ""),
                "relation": rel.get("label", rel.get("relation", "")),
                "target": rel.get("target", "")
            })

        # RAG 来源
        for chunk in chunks[:5]:
            sources["rag"]["chunks"].append({
                "text": chunk.get("text", "")[:200] + "..." if len(chunk.get("text", "")) > 200 else chunk.get("text", ""),
                "score": round(chunk.get("score", 0), 3),
                "doc_id": chunk.get("metadata", {}).get("doc_id", "")
            })

        return sources

    def ask(
        self,
        question: str,
        mode: str = "auto",
        n_hops: int = 1,
        top_k: Optional[int] = None
    ) -> QAResponse:
        """
        回答问题

        Args:
            question: 用户问题
            mode: 检索模式 ("auto", "kg_only", "rag_only", "hybrid", "kg_first", "rag_first")
            n_hops: KG 检索跳数
            top_k: RAG 检索数量

        Returns:
            QAResponse 对象
        """
        # 获取 tracer 和 session 信息
        phoenix_tracer = get_phoenix_tracer()
        tracer = trace.get_tracer(__name__)

        # 创建主 span 用于追踪整个问答流程
        with tracer.start_as_current_span("qa_engine.ask") as span:
            # 添加 session 属性
            phoenix_tracer.add_session_attributes(span)

            # 添加问答相关属性
            span.set_attribute("question", question)
            span.set_attribute("mode", mode)
            span.set_attribute("n_hops", n_hops)
            if top_k:
                span.set_attribute("top_k", top_k)

            # 执行检索
            retrieval_result = self.retriever.retrieve(
                question=question,
                mode=mode,
                n_hops=n_hops,
                top_k=top_k
            )

            # 记录检索结果统计
            span.set_attribute("retrieval.entities_count", len(retrieval_result["entities"]))
            span.set_attribute("retrieval.relations_count", len(retrieval_result["relations"]))
            span.set_attribute("retrieval.chunks_count", len(retrieval_result["chunks"]))
            span.set_attribute("retrieval.strategy", retrieval_result["strategy"])

            entities = retrieval_result["entities"]
            relations = retrieval_result["relations"]
            chunks = retrieval_result["chunks"]
            strategy = retrieval_result["strategy"]
            query_type = retrieval_result.get("query_type")

            # 根据策略选择 prompt
            if strategy == "kg_only":
                if not entities and not relations:
                    answer = "抱歉，在知识图谱中没有找到相关信息。"
                else:
                    prompt = get_kg_answer_prompt(question, entities, relations)
                    answer = self._generate_answer(prompt)

            elif strategy == "rag_only":
                if not chunks:
                    answer = "抱歉，在文档中没有找到相关信息。"
                else:
                    prompt = get_rag_answer_prompt(question, chunks)
                    answer = self._generate_answer(prompt)

            elif strategy == "kg_first":
                if entities or relations:
                    # KG 信息充足，主要用 KG
                    if chunks:
                        prompt = get_hybrid_answer_prompt(question, entities, relations, chunks)
                    else:
                        prompt = get_kg_answer_prompt(question, entities, relations)
                    answer = self._generate_answer(prompt)
                elif chunks:
                    # KG 不足，用 RAG
                    prompt = get_rag_answer_prompt(question, chunks)
                    answer = self._generate_answer(prompt)
                else:
                    answer = "抱歉，没有找到相关信息。"

            elif strategy == "rag_first":
                if chunks:
                    # RAG 信息充足
                    if entities or relations:
                        prompt = get_hybrid_answer_prompt(question, entities, relations, chunks)
                    else:
                        prompt = get_rag_answer_prompt(question, chunks)
                    answer = self._generate_answer(prompt)
                elif entities or relations:
                    # RAG 不足，用 KG
                    prompt = get_kg_answer_prompt(question, entities, relations)
                    answer = self._generate_answer(prompt)
                else:
                    answer = "抱歉，没有找到相关信息。"

            else:  # hybrid
                if entities or relations or chunks:
                    prompt = get_hybrid_answer_prompt(question, entities, relations, chunks)
                    answer = self._generate_answer(prompt)
                else:
                    answer = "抱歉，没有找到相关信息。请尝试上传相关文档或调整问题。"

            # 构建来源
            sources = self._build_sources(entities, relations, chunks)

            # 记录答案长度
            span.set_attribute("answer.length", len(answer))

            return QAResponse(
                answer=answer,
                sources=sources,
                query_type=query_type,
                strategy=strategy,
                entities=entities,
                relations=relations,
                chunks=chunks
            )

    def search(
        self,
        query: str,
        search_type: str = "all",
        top_k: int = 10
    ) -> Dict:
        """
        语义搜索

        Args:
            query: 搜索查询
            search_type: 搜索类型 ("all", "chunks", "entities")
            top_k: 返回数量

        Returns:
            搜索结果
        """
        results = {
            "query": query,
            "chunks": [],
            "entities": []
        }

        from vector_store import get_vector_store
        vector_store = get_vector_store()

        if search_type in ("all", "chunks"):
            results["chunks"] = vector_store.search_chunks(query, top_k=top_k)

        if search_type in ("all", "entities"):
            results["entities"] = vector_store.search_entities(query, top_k=top_k)

        return results

    def get_entity_detail(self, entity_name: str) -> Dict:
        """
        获取实体详情

        Args:
            entity_name: 实体名称

        Returns:
            实体详情
        """
        context = self.retriever.get_entity_context(entity_name, n_hops=2)

        # 生成实体摘要
        if context["entity"]:
            entity = context["entity"]
            related = context["related_entities"][:5]
            relations = context["relations"][:10]

            summary_prompt = f"""请为以下实体生成一段简短的介绍（50-100字）：

实体: {entity.get('label', '')} ({entity.get('type', 'Entity')})
描述: {entity.get('description', '无')}

相关实体:
{', '.join([e.get('label', '') for e in related])}

相关关系:
{chr(10).join([f"- {r.get('source', '')} -> {r.get('label', '')} -> {r.get('target', '')}" for r in relations[:5]])}
"""
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是知识图谱助手，生成简洁的实体介绍。"},
                        {"role": "user", "content": summary_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=200
                )
                summary = response.choices[0].message.content.strip()
            except Exception:
                summary = entity.get("description", "")

            context["summary"] = summary

        return context


# 单例
_qa_engine: Optional[QAEngine] = None


def get_qa_engine() -> QAEngine:
    """获取问答引擎实例（单例）"""
    global _qa_engine
    if _qa_engine is None:
        _qa_engine = QAEngine()
    return _qa_engine


# 命令行测试
if __name__ == "__main__":
    engine = get_qa_engine()

    # 测试问答
    test_questions = [
        ("李笑来是谁？", "auto"),
        ("介绍一下定投策略", "auto"),
        ("为什么要长期持有？", "hybrid"),
    ]

    for question, mode in test_questions:
        print(f"\n{'='*50}")
        print(f"问题: {question}")
        print(f"模式: {mode}")
        print("-" * 50)

        response = engine.ask(question, mode=mode)

        print(f"查询类型: {response.query_type}")
        print(f"策略: {response.strategy}")
        print(f"答案:\n{response.answer}")
        print(f"\n来源:")
        print(f"  KG 实体: {len(response.sources['kg']['entities'])}")
        print(f"  KG 关系: {len(response.sources['kg']['relations'])}")
        print(f"  RAG 片段: {len(response.sources['rag']['chunks'])}")
