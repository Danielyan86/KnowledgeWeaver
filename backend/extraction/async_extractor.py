"""
Async Knowledge Graph Extractor
异步知识图谱提取器

核心功能：
- 使用 Gemini API 或其他 LLM API 并发调用
- 支持断点续传
- 自动重试机制
- 重叠分块处理
"""

import asyncio
import json
import re
import os
from typing import Dict, List
from pathlib import Path

from dotenv import load_dotenv
from tqdm.asyncio import tqdm

from ..retrieval.prompts.prompt_loader import get_extraction_prompt, get_document_topic_prompt
from .normalizer import KnowledgeGraphNormalizer
from .entity_filter import get_entity_filter
from ..core.observability import get_tracer


# 加载环境变量
load_dotenv()


class AsyncKnowledgeGraphExtractor:
    """异步知识图谱提取器（支持 Gemini API）"""

    def __init__(self):
        """
        初始化异步提取器
        所有配置从环境变量读取，不使用默认参数
        """
        # 从环境变量读取配置
        self.chunk_size = int(os.getenv('CHUNK_SIZE', '800'))

        # 并发控制
        max_concurrent = int(os.getenv('CONCURRENT_REQUESTS', '5'))
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # LLM 后端：gemini 或 openai（文档提取专用）
        self.backend = os.getenv('EXTRACTION_LLM_BACKEND', 'gemini')

        # 初始化客户端
        if self.backend == 'gemini':
            from google import genai
            self.client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
            self.model_name = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')
        else:  # openai 兼容
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                base_url=os.getenv('LLM_BINDING_HOST'),
                api_key=os.getenv('LLM_BINDING_API_KEY')
            )
            self.model_name = os.getenv('LLM_MODEL')

        # 规范化器
        self.normalizer = KnowledgeGraphNormalizer()

        # Langfuse 追踪器
        self.tracer = get_tracer()

        # 断点续传目录
        checkpoint_dir = os.getenv('CHECKPOINT_DIR')
        if checkpoint_dir is None:
            checkpoint_dir = Path(__file__).parent.parent / "data" / "checkpoints"
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def chunk_text_overlapped(self, text: str, overlap: float = None) -> List[str]:
        """
        重叠分块（避免边界丢失信息）

        Args:
            text: 原始文本
            overlap: 重叠比例，从环境变量读取

        Returns:
            文本块列表
        """
        if overlap is None:
            overlap = float(os.getenv('CHUNK_OVERLAP_RATIO', '0.5'))

        if not text:
            return []

        # 按段落分割
        paragraphs = re.split(r'\n\s*\n', text)

        chunks = []
        current_chunk = ""
        overlap_buffer = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # 如果当前段落加上已有内容超过限制，先保存当前块
            if len(current_chunk) + len(para) > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())

                # 保留重叠部分
                overlap_size = int(len(current_chunk) * overlap)
                overlap_buffer = current_chunk[-overlap_size:]
                current_chunk = overlap_buffer + para + "\n\n"
            else:
                current_chunk += para + "\n\n"

        # 添加最后一个块
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _parse_llm_response(self, response_text: str) -> Dict:
        """
        解析 LLM 响应，提取 JSON

        Args:
            response_text: LLM 的原始响应

        Returns:
            解析后的字典，包含 entities 和 relations
        """
        # 尝试找到 JSON 代码块
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接解析
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                json_str = json_match.group(0)
            else:
                return {"entities": [], "relations": []}

        try:
            result = json.loads(json_str)

            # 应用实体过滤器，提升图谱质量
            entity_filter = get_entity_filter()
            filtered_result = entity_filter.filter_graph({
                "entities": result.get("entities", []),
                "relations": result.get("relations", [])
            })

            return filtered_result
        except json.JSONDecodeError:
            return {"entities": [], "relations": []}

    async def _call_llm(self, prompt: str) -> str:
        """
        调用 LLM（支持 Gemini 和 OpenAI 兼容 API）

        自动追踪到 Langfuse

        Args:
            prompt: 完整提示文本

        Returns:
            LLM 的响应
        """
        import time

        start_time = time.time()

        try:
            if self.backend == 'gemini':
                # Gemini API（同步调用，需要在线程池中运行）
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.models.generate_content(
                        model=self.model_name,
                        contents=prompt
                    )
                )
                output_text = response.text

                # 记录 Gemini 调用信息（日志形式）
                if self.tracer.enabled:
                    latency_ms = (time.time() - start_time) * 1000
                    print(f"📊 [Gemini API] 模型: {self.model_name}, 延迟: {round(latency_ms)}ms, "
                          f"输入: {len(prompt)} 字符, 输出: {len(output_text)} 字符")

                    # 注意：由于 Langfuse v2/v3 API 兼容性问题，
                    # Gemini 调用暂时只记录到服务器日志，不记录到 Dashboard
                    # OpenAI 兼容 API 的调用仍然会正常追踪到 Langfuse

                return output_text
            else:
                # OpenAI 兼容 API（已被 wrapper 自动追踪）
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "你是一个知识图谱提取专家，请严格按照JSON格式输出。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=2000
                )
                return response.choices[0].message.content

        except Exception as e:
            raise Exception(f"LLM 调用失败: {e}")

    async def extract_chunk_bounded(self, chunk: str, chunk_id: int, context: str = "") -> Dict:
        """
        带限流的单个块提取（异步）

        Args:
            chunk: 文本块
            chunk_id: 块 ID
            context: 上下文信息

        Returns:
            提取结果
        """
        async with self.semaphore:
            # 构建提示
            prompt = get_extraction_prompt(context + chunk if context else chunk)

            # 重试机制（指数退避）
            max_retries = int(os.getenv('MAX_RETRIES', '3'))
            for attempt in range(max_retries):
                try:
                    # 调用 LLM
                    response_text = await self._call_llm(prompt)

                    # 解析响应
                    result = self._parse_llm_response(response_text)

                    # 保存检查点
                    self._save_checkpoint(chunk_id, result)
                    return result

                except Exception as e:
                    if attempt == max_retries - 1:
                        print(f"块 {chunk_id} 处理失败: {e}")
                        return {"entities": [], "relations": []}

                    # 指数退避
                    wait_time = (2 ** attempt)
                    await asyncio.sleep(wait_time)

    def _save_checkpoint(self, chunk_id: int, result: Dict):
        """保存单个块的检查点"""
        checkpoint_file = self.checkpoint_dir / f"chunk_{chunk_id}.json"
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False)

    def _load_checkpoints(self, total_chunks: int) -> List[Dict]:
        """加载已完成的检查点"""
        results = [None] * total_chunks
        for i in range(total_chunks):
            checkpoint_file = self.checkpoint_dir / f"chunk_{i}.json"
            if checkpoint_file.exists():
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    results[i] = json.load(f)
        return results

    def _clear_checkpoints(self):
        """清理检查点文件"""
        for checkpoint_file in self.checkpoint_dir.glob("chunk_*.json"):
            checkpoint_file.unlink()

    async def _extract_document_topic(self, text: str) -> str:
        """
        提取文档主题

        Args:
            text: 文档文本（取前1000字）

        Returns:
            文档主题描述
        """
        sample = text[:1000] if len(text) > 1000 else text

        try:
            prompt = get_document_topic_prompt(sample)
            response = await self._call_llm(prompt)
            return response.strip()
        except Exception:
            return ""

    def merge_graphs(self, graphs: List[Dict], connect_islands: bool = True) -> Dict:
        """
        合并多个提取结果

        Args:
            graphs: 多个提取结果列表
            connect_islands: 是否尝试连接孤岛

        Returns:
            合并后的图谱数据
        """
        all_entities = {}  # name -> entity
        all_relations = []
        seen_relations = set()

        for graph in graphs:
            # 合并实体
            for entity in graph.get("entities", []):
                name = entity.get("name", "").strip()
                if not name:
                    continue

                if name not in all_entities:
                    all_entities[name] = {
                        "name": name,
                        "type": entity.get("type", "Entity"),
                        "description": entity.get("description", "")
                    }
                else:
                    # 合并描述
                    existing = all_entities[name]
                    if entity.get("description") and not existing.get("description"):
                        existing["description"] = entity.get("description")

            # 合并关系
            for relation in graph.get("relations", []):
                source = relation.get("source", "").strip()
                target = relation.get("target", "").strip()
                rel = relation.get("relation", "").strip()

                if not source or not target or not rel:
                    continue

                # 去重
                rel_key = f"{source}-{rel}->{target}"
                if rel_key not in seen_relations:
                    seen_relations.add(rel_key)
                    all_relations.append({
                        "source": source,
                        "relation": rel,
                        "target": target
                    })

        return {
            "entities": list(all_entities.values()),
            "relations": all_relations
        }

    def _convert_to_graph_format(self, extracted: Dict) -> Dict:
        """
        将 LLM 提取的数据转换为前端期望的格式

        Args:
            extracted: LLM 提取的原始数据

        Returns:
            前端格式的图谱数据
        """
        # 构建节点
        nodes = []
        node_ids = set()

        for entity in extracted.get("entities", []):
            name = entity.get("name", "").strip()
            if not name or name in node_ids:
                continue

            node_ids.add(name)
            nodes.append({
                "id": name,
                "label": name,
                "type": entity.get("type", "Entity"),
                "description": entity.get("description", ""),
                "properties": {},
                "degree": 0
            })

        # 构建边
        edges = []
        for relation in extracted.get("relations", []):
            source = relation.get("source", "").strip()
            target = relation.get("target", "").strip()
            rel = relation.get("relation", "").strip()

            if not source or not target or source == target:
                continue

            # 确保源节点存在
            if source not in node_ids:
                node_ids.add(source)
                nodes.append({
                    "id": source,
                    "label": source,
                    "type": "Entity",
                    "description": "",
                    "properties": {},
                    "degree": 0
                })

            # 确保目标节点存在
            if target not in node_ids:
                node_ids.add(target)
                nodes.append({
                    "id": target,
                    "label": target,
                    "type": "Entity",
                    "description": "",
                    "properties": {},
                    "degree": 0
                })

            edges.append({
                "source": source,
                "target": target,
                "label": rel,
                "weight": 1
            })

        # 计算节点度数
        degree_map = {}
        for edge in edges:
            degree_map[edge["source"]] = degree_map.get(edge["source"], 0) + 1
            degree_map[edge["target"]] = degree_map.get(edge["target"], 0) + 1

        for node in nodes:
            node["degree"] = degree_map.get(node["id"], 0)

        return {"nodes": nodes, "edges": edges}

    async def extract_document_async(self, file_path: str, resume: bool = True,
                                     return_chunks: bool = False,
                                     progress_callback: callable = None,
                                     cancellation_check: callable = None) -> Dict:
        """
        异步文档处理（支持断点续传和中断）

        Args:
            file_path: 文档路径
            resume: 是否从断点续传
            return_chunks: 是否返回原始 chunks（用于 RAG 索引）
            progress_callback: 进度回调函数 callback(current, total, stage)
            cancellation_check: 中断检查函数 cancellation_check() -> bool

        Returns:
            提取并规范化后的图谱数据

        Raises:
            Exception: 如果处理被中断
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 读取文件内容
        if path.suffix.lower() == '.txt':
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
        elif path.suffix.lower() == '.pdf':
            raise NotImplementedError("PDF 解析尚未实现")
        else:
            raise ValueError(f"不支持的文件格式: {path.suffix}")

        # 提取文档主题
        doc_topic = await self._extract_document_topic(text)
        if doc_topic:
            print(f"文档主题: {doc_topic}")

        # 分块（重叠）
        chunks = self.chunk_text_overlapped(text)
        total = len(chunks)
        print(f"文档分成 {total} 个块（重叠分块）")

        # 初始化进度
        if progress_callback:
            progress_callback(0, total, "分块完成")

        # 加载已完成的检查点
        results = self._load_checkpoints(total) if resume else [None] * total
        completed = sum(1 for r in results if r is not None)
        print(f"已完成 {completed}/{total} 块，继续处理剩余部分...")

        # 更新进度（已完成的检查点）
        if progress_callback and completed > 0:
            progress_callback(completed, total, "恢复断点")

        # 收集核心实体作为上下文
        core_entities = set()
        for result in results:
            if result:
                for entity in result.get("entities", []):
                    name = entity.get("name", "")
                    if name and len(name) <= 10:
                        core_entities.add(name)

        # 创建任务（只处理未完成的块）
        tasks = []
        for i, chunk in enumerate(chunks):
            if results[i] is None:
                # 构建上下文
                context = ""
                if doc_topic:
                    context += f"文档背景：{doc_topic}\n"
                if core_entities:
                    context += f"已识别的核心实体：{', '.join(list(core_entities)[:10])}\n"
                    context += "请注意：如果当前文本与这些实体相关，请建立关系连接。\n\n"

                tasks.append((i, self.extract_chunk_bounded(chunk, i, context)))

        # 并发执行（带进度条）
        if tasks:
            print(f"开始异步处理 {len(tasks)} 个未完成的块...")
            for idx, (i, task_coro) in enumerate(tqdm(tasks, desc="提取知识图谱")):
                # 检查是否被取消
                if cancellation_check and cancellation_check():
                    print(f"\n⚠️  处理被用户中断 (已完成 {completed + idx}/{total} 块)")
                    raise Exception("处理被用户中断")

                result = await task_coro
                results[i] = result

                # 更新核心实体
                for entity in result.get("entities", []):
                    name = entity.get("name", "")
                    if name and len(name) <= 10:
                        core_entities.add(name)

                # 更新进度
                if progress_callback:
                    current_completed = completed + idx + 1
                    progress_callback(current_completed, total, "提取实体和关系")

        # 更新进度：合并
        if progress_callback:
            progress_callback(total, total, "合并结果")

        # 合并结果
        merged = self.merge_graphs([r for r in results if r])
        print(f"合并后：{len(merged['entities'])} 个实体，{len(merged['relations'])} 个关系")

        # 转换为前端格式
        graph_data = self._convert_to_graph_format(merged)

        # 规范化
        normalized = self.normalizer.normalize_graph(graph_data)
        print(f"规范化后：{normalized['stats']}")

        # 清理检查点
        self._clear_checkpoints()

        # 如果需要返回 chunks 用于 RAG 索引
        if return_chunks:
            normalized["chunks"] = chunks
            normalized["doc_topic"] = doc_topic

        return normalized


# 命令行测试
if __name__ == "__main__":
    import sys

    async def main():
        extractor = AsyncKnowledgeGraphExtractor()

        if len(sys.argv) > 1:
            # 处理文件
            file_path = sys.argv[1]
            result = await extractor.extract_document_async(file_path)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            # 测试文本
            test_text = """
            李笑来在《让时间陪你慢慢变富》中主张定投策略。
            他认为定投是最适合普通人的投资方式，推荐标普500指数基金。
            长期主义是这本书的核心理念，强调时间复利的重要性。
            """

            # 创建临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(test_text)
                temp_path = f.name

            result = await extractor.extract_document_async(temp_path)
            print(json.dumps(result, ensure_ascii=False, indent=2))

            # 清理临时文件
            Path(temp_path).unlink()

    asyncio.run(main())
