"""
Knowledge Graph API Server
知识图谱 API 服务

基于 FastAPI 的 API 服务，提供：
- 图谱数据查询
- 热门标签获取
- 文档上传和处理
- 混合问答 (KG + RAG)
"""

import os
import shutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from .extraction import KnowledgeGraphExtractor, AsyncKnowledgeGraphExtractor
from .management import get_kg_manager, get_progress_tracker
from .core.storage import get_vector_store
from .retrieval import get_qa_engine


# 加载环境变量
load_dotenv()

# 初始化 Phoenix 追踪器（OpenTelemetry 自动追踪）
from .core.phoenix_observability import get_phoenix_tracer
phoenix_tracer = get_phoenix_tracer()

# 创建 FastAPI 应用
app = FastAPI(
    title="KnowledgeWeaver API",
    description="轻量级知识图谱提取和查询服务 (Neo4j)",
    version="2.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 获取存储实例
kg_manager = get_kg_manager()
vector_store = get_vector_store()
qa_engine = get_qa_engine()
progress_tracker = get_progress_tracker()

# 上传目录
UPLOAD_DIR = Path(__file__).parent.parent / "data" / "inputs" / "__enqueued__"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 前端目录
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


# Pydantic 模型
class GraphResponse(BaseModel):
    nodes: List[dict]
    edges: List[dict]


class DocumentInfo(BaseModel):
    doc_id: str
    file: str
    node_count: int
    edge_count: int
    updated_at: str


class UploadResponse(BaseModel):
    success: bool
    doc_id: str
    message: str


class StatsResponse(BaseModel):
    document_count: int
    total_nodes: int
    total_edges: int


# QA 相关模型
class QARequest(BaseModel):
    question: str
    mode: str = "auto"  # auto, kg_only, rag_only, hybrid, kg_first, rag_first
    n_hops: int = 1
    top_k: int = 5


class SourceInfo(BaseModel):
    kg: dict
    rag: dict


class QAResponse(BaseModel):
    answer: str
    sources: SourceInfo
    query_type: Optional[str]
    strategy: str


class SearchRequest(BaseModel):
    query: str
    search_type: str = "all"  # all, chunks, entities
    top_k: int = 10


class SearchResponse(BaseModel):
    query: str
    chunks: List[dict]
    entities: List[dict]


class EntityContextResponse(BaseModel):
    entity: Optional[dict]
    related_entities: List[dict]
    relations: List[dict]
    chunks: List[dict]
    summary: Optional[str]


# API 端点

@app.get("/health")
async def health_check():
    """健康检查 - Kubernetes liveness probe"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/ready")
async def readiness_check():
    """就绪检查 - Kubernetes readiness probe"""
    try:
        # 检查Neo4j连接
        neo4j_ready = kg_manager is not None
        # 检查向量存储
        vector_ready = vector_store is not None

        if neo4j_ready and vector_ready:
            return {
                "status": "ready",
                "services": {
                    "neo4j": "connected",
                    "vector_store": "connected"
                }
            }
        else:
            raise HTTPException(status_code=503, detail="Services not ready")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Not ready: {e}")


@app.get("/graph/label/popular", response_model=List[str])
async def get_popular_labels(limit: int = Query(default=30, ge=1, le=100)):
    """
    获取热门标签（从 Neo4j）

    返回按度数排序的热门节点标签列表
    """
    labels = kg_manager.get_popular_labels(limit)
    return labels


@app.get("/graphs", response_model=GraphResponse)
async def get_graphs(label: Optional[str] = Query(default=None)):
    """
    获取图谱数据（从 Neo4j）

    - 如果指定 label，返回该标签的子图
    - 如果不指定，返回全部图谱
    """
    if label:
        graph = kg_manager.get_graph_by_label(label)
    else:
        graph = kg_manager.get_all_graphs()

    return GraphResponse(
        nodes=graph.get("nodes", []),
        edges=graph.get("edges", [])
    )


@app.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """列出所有已处理的文档（从 Neo4j）"""
    docs = kg_manager.list_documents()
    return [DocumentInfo(**doc) for doc in docs]


@app.get("/documents/{doc_id}", response_model=GraphResponse)
async def get_document_graph(doc_id: str):
    """获取指定文档的图谱（从 Neo4j）"""
    graph = kg_manager.load_document(doc_id)
    if not graph or not graph.get("nodes"):
        raise HTTPException(status_code=404, detail=f"文档 {doc_id} 不存在")

    return GraphResponse(
        nodes=graph.get("nodes", []),
        edges=graph.get("edges", [])
    )


@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """删除指定文档的图谱和向量索引（从 Neo4j）"""
    # 删除图谱（从 Neo4j）
    delete_stats = kg_manager.delete_document(doc_id)

    # 删除向量索引
    deleted_vectors = vector_store.delete_by_doc(doc_id)

    if "error" in delete_stats:
        raise HTTPException(status_code=500, detail=delete_stats["error"])

    return {
        "success": True,
        "message": f"文档 {doc_id} 已删除",
        "neo4j": delete_stats.get("neo4j", {}),
        "deleted_chunks": deleted_vectors.get("chunks_deleted", 0),
        "deleted_entities": deleted_vectors.get("entities_deleted", 0)
    }


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """获取统计信息（从 Neo4j）"""
    stats = kg_manager.get_stats()

    if "error" in stats:
        return StatsResponse(
            document_count=0,
            total_nodes=0,
            total_edges=0
        )

    neo4j_stats = stats.get("neo4j", {})
    return StatsResponse(
        document_count=len(kg_manager.list_documents()),
        total_nodes=neo4j_stats.get("total_nodes", 0),
        total_edges=neo4j_stats.get("total_edges", 0)
    )


# ==================== QA API 端点 ====================

@app.post("/qa", response_model=QAResponse)
async def ask_question(request: QARequest):
    """
    混合问答接口

    支持多种检索模式：
    - auto: 自动根据问题类型选择策略
    - kg_only: 仅使用知识图谱
    - rag_only: 仅使用 RAG
    - hybrid: 混合使用
    - kg_first: KG 优先，不足时补充 RAG
    - rag_first: RAG 优先，不足时补充 KG

    注意：LLM 调用会被 Langfuse 自动追踪（通过 OpenAI wrapper）
    """
    try:
        response = qa_engine.ask(
            question=request.question,
            mode=request.mode,
            n_hops=request.n_hops,
            top_k=request.top_k
        )

        # 刷新 Langfuse 追踪，确保数据立即发送
        from .core.observability import get_tracer
        get_tracer().flush()

        return QAResponse(
            answer=response.answer,
            sources=SourceInfo(
                kg=response.sources["kg"],
                rag=response.sources["rag"]
            ),
            query_type=response.query_type,
            strategy=response.strategy
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答处理失败: {e}")


@app.post("/search", response_model=SearchResponse)
async def semantic_search(request: SearchRequest):
    """
    语义搜索接口

    搜索类型：
    - all: 搜索文档片段和实体
    - chunks: 仅搜索文档片段
    - entities: 仅搜索实体
    """
    try:
        results = qa_engine.search(
            query=request.query,
            search_type=request.search_type,
            top_k=request.top_k
        )
        return SearchResponse(**results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {e}")


@app.get("/entities/{entity_name}/context", response_model=EntityContextResponse)
async def get_entity_context(entity_name: str, n_hops: int = Query(default=2, ge=1, le=3)):
    """
    获取实体上下文

    返回实体的详细信息、相关实体、关系和相关文档片段
    """
    try:
        context = qa_engine.get_entity_detail(entity_name)
        return EntityContextResponse(
            entity=context.get("entity"),
            related_entities=context.get("related_entities", []),
            relations=context.get("relations", []),
            chunks=context.get("chunks", []),
            summary=context.get("summary")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实体上下文失败: {e}")


@app.get("/vector-stats")
async def get_vector_stats():
    """获取向量存储统计信息"""
    return vector_store.get_stats()


# ==================== 文档处理函数 ====================

def process_document(file_path: str, doc_id: str):
    """
    后台处理文档的函数

    Args:
        file_path: 文件路径
        doc_id: 文档 ID
    """
    try:
        print(f"开始处理文档: {doc_id}")
        extractor = KnowledgeGraphExtractor()

        # 提取图谱，同时返回 chunks 用于 RAG 索引
        graph = extractor.extract_from_document(file_path, return_chunks=True)

        # 获取 chunks 并移除（不保存到图谱文件）
        chunks = graph.pop("chunks", [])
        doc_topic = graph.pop("doc_topic", "")

        # 保存图谱（到 Neo4j）
        metadata = {
            "original_file": file_path,
            "processed_at": datetime.now().isoformat(),
            "doc_topic": doc_topic
        }
        save_stats = kg_manager.save_document(doc_id, graph, metadata)
        print(f"图谱保存完成: {doc_id}, 统计: {save_stats}")

        # 索引 chunks 到向量存储
        if chunks:
            print(f"开始索引 {len(chunks)} 个文本块...")
            chunk_ids = vector_store.add_chunks(
                chunks=chunks,
                doc_id=doc_id,
                metadata_list=[{"doc_topic": doc_topic} for _ in chunks]
            )
            print(f"文本块索引完成: {len(chunk_ids)} 个")

        # 索引实体到向量存储
        nodes = graph.get("nodes", [])
        if nodes:
            print(f"开始索引 {len(nodes)} 个实体...")
            entity_ids = vector_store.add_entities(nodes, doc_id)
            print(f"实体索引完成: {len(entity_ids)} 个")

        print(f"文档处理完成: {doc_id}")

    except Exception as e:
        print(f"文档处理失败: {doc_id}, 错误: {e}")


@app.post("/documents/upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    上传并处理文档

    支持 txt 和 pdf 格式
    文档将在后台异步处理
    """
    # 检查文件类型
    allowed_extensions = {'.txt', '.pdf'}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {file_ext}，支持的格式: {allowed_extensions}"
        )

    # 生成文档 ID
    doc_id = Path(file.filename).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_doc_id = f"{doc_id}_{timestamp}"

    # 保存上传的文件
    file_path = UPLOAD_DIR / f"{unique_doc_id}{file_ext}"
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {e}")

    # 添加后台任务处理文档
    background_tasks.add_task(process_document, str(file_path), unique_doc_id)

    return UploadResponse(
        success=True,
        doc_id=unique_doc_id,
        message=f"文档已上传，正在后台处理"
    )


@app.post("/documents/process/{doc_id}")
async def process_existing_document(doc_id: str, background_tasks: BackgroundTasks):
    """
    处理已存在的文档

    用于重新处理之前上传的文档
    """
    # 查找文件
    possible_files = list(UPLOAD_DIR.glob(f"{doc_id}*"))
    if not possible_files:
        raise HTTPException(status_code=404, detail=f"文档 {doc_id} 不存在")

    file_path = possible_files[0]

    # 添加后台任务
    background_tasks.add_task(process_document, str(file_path), doc_id)

    return {"success": True, "message": f"文档 {doc_id} 正在重新处理"}


# ==================== 异步文档处理 ====================

async def process_document_async(file_path: str, doc_id: str):
    """
    异步处理文档（使用 Gemini 并发）

    Args:
        file_path: 文件路径
        doc_id: 文档 ID
    """
    try:
        print(f"[异步] 开始处理文档: {doc_id}")

        # 定义进度回调
        def update_progress(current: int, total: int, stage: str):
            """更新进度"""
            if current == 0 and total > 0:
                # 初始化进度
                progress_tracker.start(doc_id, total, Path(file_path).name)
            else:
                # 更新进度
                progress_tracker.update(doc_id, current, stage)

        extractor = AsyncKnowledgeGraphExtractor()

        # 提取图谱，同时返回 chunks 用于 RAG 索引
        graph = await extractor.extract_document_async(
            file_path,
            resume=True,
            return_chunks=True,
            progress_callback=update_progress
        )

        # 获取 chunks 并移除（不保存到图谱文件）
        chunks = graph.pop("chunks", [])
        doc_topic = graph.pop("doc_topic", "")

        # 保存图谱（JSON + Neo4j 双写）
        metadata = {
            "original_file": file_path,
            "processed_at": datetime.now().isoformat(),
            "doc_topic": doc_topic,
            "processing_mode": "async_claude_cli"
        }
        save_stats = kg_manager.save_document(doc_id, graph, metadata)
        print(f"[异步] 图谱保存完成: {doc_id}, 统计: {save_stats}")

        # 索引 chunks 到向量存储
        if chunks:
            print(f"[异步] 开始索引 {len(chunks)} 个文本块...")
            chunk_ids = vector_store.add_chunks(
                chunks=chunks,
                doc_id=doc_id,
                metadata_list=[{"doc_topic": doc_topic} for _ in chunks]
            )
            print(f"[异步] 文本块索引完成: {len(chunk_ids)} 个")

        # 索引实体到向量存储
        nodes = graph.get("nodes", [])
        if nodes:
            print(f"[异步] 开始索引 {len(nodes)} 个实体...")
            entity_ids = vector_store.add_entities(nodes, doc_id)
            print(f"[异步] 实体索引完成: {len(entity_ids)} 个")

        # 标记完成
        progress_tracker.complete(doc_id, {
            "nodes": len(graph.get("nodes", [])),
            "edges": len(graph.get("edges", [])),
            "chunks": len(chunks) if chunks else 0
        })

        print(f"[异步] 文档处理完成: {doc_id}")

    except Exception as e:
        # 标记失败
        progress_tracker.fail(doc_id, str(e))
        print(f"[异步] 文档处理失败: {doc_id}, 错误: {e}")
        import traceback
        traceback.print_exc()


@app.post("/documents/upload-async", response_model=UploadResponse)
async def upload_document_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    异步上传并处理文档（使用 Claude CLI 并发）

    支持 txt 和 pdf 格式
    使用异步并发处理，速度提升 3-5 倍
    支持断点续传
    """
    # 检查文件类型
    allowed_extensions = {'.txt', '.pdf'}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {file_ext}，支持的格式: {allowed_extensions}"
        )

    # 生成文档 ID
    doc_id = Path(file.filename).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_doc_id = f"{doc_id}_{timestamp}"

    # 保存上传的文件
    file_path = UPLOAD_DIR / f"{unique_doc_id}{file_ext}"
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {e}")

    # 添加后台任务（异步处理）
    background_tasks.add_task(process_document_async, str(file_path), unique_doc_id)

    return UploadResponse(
        success=True,
        doc_id=unique_doc_id,
        message=f"文档已上传，正在使用异步并发处理"
    )


@app.get("/documents/progress/{doc_id}")
async def get_document_progress(doc_id: str):
    """
    获取文档处理进度

    Args:
        doc_id: 文档 ID

    Returns:
        进度信息
    """
    progress = progress_tracker.get(doc_id)

    if not progress:
        raise HTTPException(status_code=404, detail=f"未找到文档 {doc_id} 的处理进度")

    return progress


# 挂载静态文件目录（放在所有API路由之后）
# 这样API路由优先匹配，静态文件作为fallback
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


# 主程序入口
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "9621"))
    host = os.getenv("HOST", "0.0.0.0")

    print(f"启动服务: http://{host}:{port}")
    print(f"API 文档: http://{host}:{port}/docs")

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False  # 相对导入时不支持 reload
    )
