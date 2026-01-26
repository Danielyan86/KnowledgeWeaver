# KnowledgeWeaver - 项目配置文档

## 项目概述

KnowledgeWeaver 是一个智能问答系统，结合知识图谱（KG）和检索增强生成（RAG）技术，自动从文档中提取实体和关系，构建知识图谱，并通过混合检索提供准确的上下文感知答案。

### 核心特性

- ✅ **异步并发处理**：使用 Claude CLI 并发处理文档块，速度提升 3-5 倍
- ✅ **断点续传**：支持中断后恢复处理
- ✅ **进度追踪**：实时显示处理进度和状态
- ✅ **Neo4j 存储**：高性能图数据库，支持复杂图查询和内置算法
- ✅ **向量检索**：ChromaDB 向量存储，支持语义搜索
- ✅ **混合检索**：向量相似度 + 图结构检索
- ✅ **模块化架构**：分层包结构，易于维护和扩展

## 技术栈

### 后端
- **FastAPI**：高性能 Web 框架
- **Claude CLI**：通过 subprocess 调用，支持包月套餐
- **Neo4j**：图数据库，支持 GDS 算法库
- **ChromaDB**：向量数据库
- **asyncio**：异步并发处理

### 前端
- **D3.js**：知识图谱可视化
- **JavaScript**：交互逻辑

## 项目结构

```
KnowledgeWeaver/
├── backend/
│   ├── core/                      # 核心模块
│   │   ├── config.py             # 配置管理（提示词模板、参数等）
│   │   ├── embeddings/           # 嵌入服务
│   │   │   └── service.py        # 文本嵌入服务
│   │   └── storage/              # 存储层
│   │       ├── neo4j.py         # Neo4j 图存储
│   │       └── vector.py        # ChromaDB 向量存储
│   │
│   ├── extraction/               # 知识提取模块
│   │   ├── async_extractor.py   # 异步提取器（Claude CLI 并发）
│   │   ├── extractor.py         # 同步提取器（备用）
│   │   ├── normalizer.py        # 图谱规范化（去重、合并）
│   │   └── entity_filter.py     # 实体过滤
│   │
│   ├── retrieval/                # 检索模块
│   │   ├── hybrid_retriever.py  # 混合检索器（KG + RAG）
│   │   ├── qa_engine.py         # 问答引擎
│   │   └── prompts/             # 提示词管理
│   │       ├── extraction_prompts.py  # 提取提示词
│   │       ├── qa_prompts.py         # 问答提示词
│   │       └── prompt_loader.py      # 提示词加载器
│   │
│   ├── management/               # 管理模块
│   │   ├── kg_manager.py        # 知识图谱统一管理
│   │   └── progress_tracker.py  # 进度追踪
│   │
│   └── server.py                 # FastAPI 服务入口
│
├── data/
│   ├── storage/
│   │   └── vector_db/           # 向量数据库
│   ├── checkpoints/             # 断点续传检查点
│   ├── progress/                # 进度追踪数据
│   └── inputs/                  # 用户上传文件
│       └── __enqueued__/        # 待处理文件队列
│
├── frontend/                     # 前端代码
│   ├── index.html
│   └── kg-*.js                  # 可视化脚本
│
├── tests/                        # 测试用例
│   ├── test_*.py                # 测试脚本
│   └── data/                    # 测试数据
│
├── docs/                         # 文档
│   ├── NEO4J_GUIDE.md           # Neo4j 使用指南
│   ├── LANGFUSE_*.md            # Langfuse 相关文档
│   ├── architecture-*.png       # 架构图
│   └── *.md                     # 其他文档
│
├── docker/                       # Docker 相关配置
│   └── docker-compose.*.yml     # Docker Compose 文件
│
├── scripts/                      # 脚本工具
│   ├── migrate_*.sh             # 数据迁移脚本
│   └── test_*.sh                # 测试脚本
│
├── logs/                         # 日志文件（运行时生成）
│   ├── *.log                    # 服务日志
│   └── *.pid                    # 进程ID文件
│
├── tools/                        # 开发工具
│   └── code_checker.py          # 代码检查工具
│
├── .env                          # 环境配置（不提交）
├── .env.example                  # 环境配置示例
├── requirements.txt              # Python 依赖
├── CLAUDE.md                     # 项目配置文档
└── README.md                     # 项目说明
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件：

```bash
# Claude CLI 配置（使用包月套餐）
CLAUDE_CLI_PATH=claude
CONCURRENT_REQUESTS=5
MAX_RETRIES=3

# 或者使用自定义 LLM Endpoint
LLM_BINDING_HOST=https://space.ai-builders.com/backend/v1
LLM_BINDING_API_KEY=your_api_key_here
LLM_MODEL=deepseek

# Neo4j 配置
USE_NEO4J=true
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# 服务配置
HOST=0.0.0.0
PORT=9621
```

### 3. 启动 Neo4j

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

访问 http://localhost:7474 查看 Neo4j 浏览器。

### 4. 启动服务

```bash
cd backend
python server.py
```

服务将在 `http://localhost:9621` 启动。

### 5. 处理文档

#### 方式 1：异步 API（推荐）
```bash
curl -X POST "http://localhost:9621/documents/upload-async" \
  -F "file=@your_book.txt"
```

#### 方式 2：同步 API
```bash
curl -X POST "http://localhost:9621/documents/upload" \
  -F "file=@your_book.txt"
```

#### 方式 3：命令行
```bash
python backend/extraction/async_extractor.py your_book.txt
```

## 核心功能说明

### 异步并发处理

使用 Claude CLI 通过 subprocess 并发处理文档块：

```python
# 配置并发数
CONCURRENT_REQUESTS=5  # 同时处理 5 个文本块

# 处理流程
文档 (160KB)
  ↓ 分块（重叠 50%）
  ↓ 200 个文本块
  ↓ 并发处理（5 个一组）
  ↓ 40 批次 × 2秒 = 80秒
  ↓ 合并 + 规范化
  ↓ Neo4j + 向量存储
```

**性能对比：**
- 串行处理：200 块 × 2秒 = 6-10 分钟
- 并发处理：200 块 ÷ 5 = 40 批 × 2秒 = **1.5-2 分钟**
- **提升 3-5 倍**

### 进度追踪

实时追踪文档处理进度：

```bash
# 查询进度
curl http://localhost:9621/documents/progress/{doc_id}

# 返回示例
{
  "status": "processing",
  "current": 50,
  "total": 200,
  "percentage": 25.0,
  "stage": "提取实体和关系",
  "filename": "book.txt"
}
```

### 断点续传

处理过程中会自动保存检查点：

```bash
data/checkpoints/{doc_id}/
├── chunk_0.json
├── chunk_1.json
└── ...
```

中断后重新上传同一文件，系统会自动从断点继续。

### Neo4j 图存储

#### 增量更新机制

- **节点（实体）**：跨文档共享，使用 `doc_ids` 数组
  ```cypher
  {
    id: "李笑来",
    type: "Person",
    doc_ids: ["book1", "book2"],  // 可属于多个文档
    created_at: datetime(),
    updated_at: datetime()
  }
  ```

- **关系**：文档特定，使用单个 `doc_id`
  ```cypher
  (李笑来)-[RELATES {
    label: "著作",
    doc_id: "book1",  // 单个文档
    weight: 1
  }]->(让时间陪你慢慢变富)
  ```

#### 智能去重

- 相同实体只存一份
- 不同文档可以共享实体
- 删除文档时，只删除该文档的关系和孤立节点

### 向量存储

ChromaDB 存储两类数据：

1. **文档片段（Chunks）**：用于语义检索
   ```python
   {
     "text": "文本内容...",
     "doc_id": "book1",
     "metadata": {"doc_topic": "投资理财"}
   }
   ```

2. **实体（Entities）**：用于实体检索
   ```python
   {
     "id": "李笑来",
     "type": "Person",
     "description": "投资者、作家",
     "doc_id": "book1"
   }
   ```

### 提示词管理

提示词使用 Python 配置文件管理（`backend/core/config.py`）：

```python
# 实体提取提示词
ENTITY_EXTRACTION_PROMPT = """
你是一个知识图谱实体提取专家。

## 实体提取规则：
1. 节点名必须是短名词（≤10字）
2. 节点类型明确（Person/Book/Concept/Strategy...）
3. 只提取名词性实体，不提取句子或观点

## 待提取文本：
{text}
"""
```

**修改提示词：**
1. 编辑 `backend/core/config.py`
2. 修改对应的提示词模板
3. 重启服务

## 配置说明

### 并发配置

```bash
# 并发数（推荐 3-10）
CONCURRENT_REQUESTS=5

# 重试次数
MAX_RETRIES=3

# 分块大小
CHUNK_SIZE=800

# 重叠比例（避免边界信息丢失）
CHUNK_OVERLAP_RATIO=0.5
```

### Neo4j 配置

```bash
# 启用 Neo4j
USE_NEO4J=true

# 连接配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# 性能配置
NEO4J_MAX_POOL_SIZE=50
NEO4J_BATCH_SIZE=500
```

## API 端点

### 文档管理

- `POST /documents/upload-async` - 异步上传文档（推荐）
- `POST /documents/upload` - 同步上传文档
- `GET /documents` - 列出所有文档
- `GET /documents/{doc_id}` - 获取文档图谱
- `GET /documents/progress/{doc_id}` - 获取处理进度
- `DELETE /documents/{doc_id}` - 删除文档

### 图谱查询

- `GET /graphs` - 获取全部图谱
- `GET /graphs?label={label}` - 获取子图
- `GET /graph/label/popular` - 获取热门标签

### 问答

- `POST /qa` - 混合问答
  - `mode`: auto, kg_only, rag_only, hybrid, kg_first, rag_first
  - `n_hops`: 图查询跳数
  - `top_k`: 检索结果数量
- `POST /search` - 语义搜索
  - `search_type`: all, chunks, entities
- `GET /entities/{entity_name}/context` - 获取实体上下文

### 统计

- `GET /stats` - 获取图谱统计信息
- `GET /vector-stats` - 获取向量存储统计

## Neo4j 使用指南

### 内置图算法（GDS）

Neo4j 提供 60+ 种现成算法，详见 `docs/NEO4J_GUIDE.md`。

**常用算法示例：**

```cypher
-- 1. 创建图投影（只需一次）
CALL gds.graph.project('knowledge-graph', 'Entity', 'RELATES')

-- 2. PageRank：找出最重要的概念
CALL gds.pageRank.stream('knowledge-graph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).id AS entity, score
ORDER BY score DESC LIMIT 10

-- 3. Louvain：发现知识聚类
CALL gds.louvain.stream('knowledge-graph')
YIELD nodeId, communityId
RETURN gds.util.asNode(nodeId).id AS entity, communityId

-- 4. Node Similarity：推荐相似概念
MATCH (source:Entity {id: "定投"})
CALL gds.nodeSimilarity.stream('knowledge-graph', {
  topK: 5,
  sourceNodeFilter: [source]
})
YIELD node2, similarity
RETURN gds.util.asNode(node2).id AS similar_concept, similarity

-- 5. Shortest Path：概念关联路径
MATCH (start:Entity {id: "定投"}), (end:Entity {id: "普通人"})
CALL gds.shortestPath.dijkstra.stream('knowledge-graph', {
  sourceNode: start,
  targetNode: end
})
YIELD path
RETURN [node in nodes(path) | node.id] AS path
```

### 常用查询

```cypher
-- 查询实体所属文档
MATCH (n:Entity {id: "李笑来"})
RETURN n.doc_ids

-- 查询某文档的所有实体
MATCH (n:Entity)
WHERE "book1" IN n.doc_ids
RETURN n

-- 查询跨文档共享的实体
MATCH (n:Entity)
WHERE size(n.doc_ids) > 1
RETURN n.id, n.doc_ids
ORDER BY size(n.doc_ids) DESC

-- 统计每个实体的文档数
MATCH (n:Entity)
RETURN n.id, size(n.doc_ids) as doc_count
ORDER BY doc_count DESC LIMIT 10
```

## 常见问题

### Q: 为什么使用 Claude CLI？
A: Claude CLI 可以使用包月套餐，成本更低。通过 subprocess 并发调用，性能与 API SDK 相当。

### Q: 并发数如何设置？
A: 建议从 5 开始。过高可能触发限流，过低速度提升不明显。根据您的套餐限制调整。

### Q: Neo4j 是必需的吗？
A: 推荐使用。Neo4j 提供高性能图查询和 60+ 种内置算法，大幅提升系统能力。

### Q: 如何查看处理进度？
A:
1. 调用 `/documents/progress/{doc_id}` API
2. 查看 `data/progress/` 目录
3. 查看 `data/checkpoints/` 目录的文件数量

### Q: 断点续传如何工作？
A: 每处理完一个文本块，结果保存到 `data/checkpoints/{doc_id}/chunk_{id}.json`。重新处理时跳过已完成的块。

### Q: 同一本书处理两次会怎么样？
A: 采用覆盖模式，旧版本数据会被新版本完全替换。共享的实体会保留。

### Q: 不同书有相同实体怎么办？
A: 实体会被共享，`doc_ids` 数组会包含所有相关文档。每个文档的关系独立存储。

### Q: 如何修改提示词？
A: 编辑 `backend/core/config.py` 文件中的提示词模板，重启服务即可。

## 性能优化建议

### 1. 并发数调整

```bash
# 小文档（< 50 块）
CONCURRENT_REQUESTS=3

# 中等文档（50-200 块）
CONCURRENT_REQUESTS=5

# 大文档（> 200 块）
CONCURRENT_REQUESTS=10
```

### 2. 分块配置

```bash
# 技术文档（逻辑紧密）
CHUNK_SIZE=600
CHUNK_OVERLAP_RATIO=0.6

# 小说（上下文松散）
CHUNK_SIZE=1000
CHUNK_OVERLAP_RATIO=0.3
```

### 3. Neo4j 优化

```bash
# 大规模数据
NEO4J_MAX_POOL_SIZE=100
NEO4J_BATCH_SIZE=1000

# 创建索引（在 Neo4j 浏览器中执行）
CREATE INDEX entity_id_index FOR (n:Entity) ON (n.id)
CREATE INDEX entity_type_index FOR (n:Entity) ON (n.type)
```

## 开发指南

### 模块化架构

项目采用分层包结构，每个模块职责清晰：

- `core/`: 核心功能（配置、存储、嵌入）
- `extraction/`: 知识提取
- `retrieval/`: 检索和问答
- `management/`: 管理功能

### 添加新功能

1. **新的存储后端**：在 `core/storage/` 添加新文件
2. **新的提取策略**：在 `extraction/` 添加新提取器
3. **新的检索方式**：在 `retrieval/` 添加新检索器
4. **新的管理功能**：在 `management/` 添加新管理器

### 统一接口

所有存储操作通过 `KnowledgeGraphManager` 统一管理：

```python
from backend.management import get_kg_manager

kg_manager = get_kg_manager()

# 保存文档
kg_manager.save_document(doc_id, graph, metadata)

# 加载文档
graph = kg_manager.load_document(doc_id)

# 删除文档
kg_manager.delete_document(doc_id)
```

### 文档规范

**重要规则：所有生成的文档必须放在 `docs/` 目录下，不要放在项目根目录。**

- 技术文档：`docs/技术文档名.md`
- 设计文档：`docs/设计文档名.md`
- 使用指南：`docs/指南名.md`
- 架构图等：`docs/图片名.png`

保持项目根目录整洁，只保留必要的配置文件（如 `CLAUDE.md`、`README.md`、`.env` 等）。

## 监控和日志

### 日志位置

- 服务日志：控制台输出
- 处理日志：`[异步]` 前缀
- 错误日志：自动打印堆栈

### 监控指标

```python
# 获取统计信息
GET /stats

# 返回
{
  "document_count": 10,
  "total_nodes": 5000,
  "total_edges": 8000
}

# 向量存储统计
GET /vector-stats

# 返回
{
  "total_chunks": 1500,
  "total_entities": 500
}
```

## 测试

### 自动化测试

```bash
# 运行单元测试
pytest tests/

# 运行集成测试
python tests/test_upload.py
```

### 手动测试

参考 `backend/TEST_REPORT.md` 查看测试报告和测试脚本。

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

---

**更新日期**: 2026-01-26
**维护者**: Sheldon
**版本**: 2.0.0 (模块化重构版)
