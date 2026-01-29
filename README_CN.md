# KnowledgeWeaver

知识图谱 + RAG 混合问答系统

中文 | [English](README.md)

## 项目简介

KnowledgeWeaver 是一个结合了知识图谱（Knowledge Graph）和检索增强生成（RAG）技术的智能问答系统。系统能够从文档中自动提取实体和关系，构建知识图谱，并通过向量检索和图谱推理相结合的方式，提供准确、有上下文的问答服务。

## 核心功能

- **文档处理**：支持 PDF 和 TXT 格式文档的自动解析和分块
- **知识提取**：基于 LLM 的实体和关系抽取
- **知识图谱**：自动构建、规范化和存储知识图谱
- **混合检索**：结合向量相似度检索和图谱结构检索
- **智能问答**：基于检索结果的上下文感知问答
- **可视化**：基于 D3.js 的交互式知识图谱可视化

## 系统架构

### 应用架构

![系统架构图](docs/architecture/architecture-cn.png)

### AWS 部署架构

AWS 部署架构和基础设施设计，请查看：
- [交互式 AWS 架构图](docs/architecture/aws-architecture-diagram-cn.html)
- [AWS 部署指南](docs/deployment/AWS_DEPLOYMENT_GUIDE.md)

### 处理流程

1. **输入层**：接收文档（txt/pdf）
2. **处理层**：
   - 文档分块
   - LLM 实体和关系提取
   - 知识合并和规范化
3. **存储层**：
   - Neo4j 图数据库（知识图谱存储）
   - ChromaDB 向量数据库（语义搜索）
4. **服务层**：
   - FastAPI 后端服务
   - 混合检索器（KG + RAG）
   - QA 引擎
5. **前端层**：
   - D3.js 知识图谱可视化
   - 聊天问答界面

## 技术栈

### 后端
- **FastAPI**：高性能 Web 框架
- **LLM 集成**：OpenAI API / 自定义端点
- **Neo4j**：图数据库，用于知识图谱存储
- **ChromaDB**：向量数据库，用于语义搜索
- **Jinja2**：提示词模板引擎

### 前端
- **D3.js**：知识图谱可视化
- **JavaScript**：交互逻辑

### 外部服务
- **LLM API**：space.ai-builders.com

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

创建 `.env` 文件并配置：

```bash
# LLM 配置
LLM_BINDING_HOST=https://space.ai-builders.com/backend/v1
LLM_BINDING_API_KEY=your_api_key_here

# Neo4j 配置
USE_NEO4J=true
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
```

### 启动服务

**方式 1: 快速启动（推荐开发环境）**
```bash
./scripts/start_dev.sh
```

**方式 2: 完整启动（推荐首次运行）**
```bash
./scripts/start.sh
```

**方式 3: 手动启动**
```bash
python -m backend.server
```

**其他命令:**
```bash
# 查看服务状态
./scripts/status.sh

# 停止服务
./scripts/stop.sh

# 重启服务
./scripts/restart.sh
```

详细文档请参考 [scripts/README.md](scripts/README.md)。

### 访问服务

- **前端界面**: http://localhost:9621
- **API 文档**: http://localhost:9621/docs
- **健康检查**: http://localhost:9621/health

### 处理文档

```bash
python backend/process_book.py
```

## 使用指南

### 启动本地服务

#### 1. 启动 Neo4j 数据库

**方式 A: Docker（推荐）**

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  -v $(pwd)/data/neo4j/data:/data \
  neo4j:latest
```

访问 Neo4j 浏览器：http://localhost:7474

**方式 B: 原生安装**

从官网下载并安装：https://neo4j.com/download/

#### 2. 启动 FastAPI 后端

```bash
python -m backend.server
```

API 将在以下地址启动：http://localhost:9621

- API 文档：http://localhost:9621/docs
- 健康检查：http://localhost:9621/health

#### 3. （可选）启动可观测性工具

**方式 A: Langfuse - 生产环境监控**

Langfuse 提供详细的 LLM 调用追踪、成本分析和生产监控。

```bash
# 1. 在 .env 中配置环境变量
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=https://cloud.langfuse.com  # 或自托管 URL

# 2. 安装 Langfuse
pip install langfuse>=2.0.0

# 3. 重启后端服务
python -m backend.server
```

访问 https://cloud.langfuse.com 查看追踪数据。

自托管部署请参考：[Langfuse 完整指南](docs/observability/LANGFUSE_GUIDE.md)

**方式 B: Phoenix - 开发和评估**

Phoenix 提供零代码追踪、实验管理和提示词优化。

```bash
# 1. 启动 Phoenix 服务器（Docker）
docker run -d \
  --name phoenix \
  -p 6006:6006 \
  -p 4317:4317 \
  -v $(pwd)/data/phoenix:/data \
  arizephoenix/phoenix:latest

# 2. 在 .env 中配置环境变量
PHOENIX_ENABLED=true
PHOENIX_ENDPOINT=http://localhost:6006/v1/traces

# 3. 安装 Phoenix 包
pip install arize-phoenix arize-phoenix-otel openinference-instrumentation-openai

# 4. 重启后端服务
python -m backend.server
```

访问 Phoenix 界面：http://localhost:6006

详细设置和对比请参考：[Phoenix 集成指南](docs/observability/PHOENIX_INTEGRATION.md)

### 使用系统

#### 上传和处理文档

**通过 API（异步 - 推荐）**

```bash
curl -X POST "http://localhost:9621/documents/upload-async" \
  -F "file=@your_document.txt"

# 响应：{"doc_id": "abc123", "status": "processing"}

# 查询进度
curl "http://localhost:9621/documents/progress/abc123"
```

**通过 API（同步）**

```bash
curl -X POST "http://localhost:9621/documents/upload" \
  -F "file=@your_document.pdf"
```

**通过命令行**

```bash
python backend/extraction/async_extractor.py path/to/document.txt
```

#### 查询知识图谱

**提问**

```bash
curl -X POST "http://localhost:9621/qa" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "什么是知识图谱？",
    "mode": "auto",
    "n_hops": 2,
    "top_k": 5
  }'
```

查询模式：
- `auto`：自动选择最佳策略
- `kg_only`：仅使用知识图谱
- `rag_only`：仅使用向量检索
- `hybrid`：结合 KG 和 RAG
- `kg_first`：优先 KG，回退到 RAG
- `rag_first`：优先 RAG，回退到 KG

**语义搜索**

```bash
curl -X POST "http://localhost:9621/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "投资策略",
    "search_type": "all",
    "top_k": 10
  }'
```

搜索类型：
- `all`：搜索文档片段和实体
- `chunks`：仅搜索文档片段
- `entities`：仅搜索实体

#### 可视化知识图谱

**获取完整图谱**

```bash
curl "http://localhost:9621/graphs"
```

**获取文档特定图谱**

```bash
curl "http://localhost:9621/documents/abc123"
```

**在浏览器中查看**

在浏览器中打开 `frontend/index.html` 与 D3.js 可视化进行交互。

#### 监控和管理

**查看统计信息**

```bash
# 知识图谱统计
curl "http://localhost:9621/stats"

# 向量存储统计
curl "http://localhost:9621/vector-stats"
```

**列出文档**

```bash
curl "http://localhost:9621/documents"
```

**删除文档**

```bash
curl -X DELETE "http://localhost:9621/documents/abc123"
```

### 配置参考

编辑 `.env` 文件自定义设置：

```bash
# === LLM 配置 ===
LLM_BINDING_HOST=https://space.ai-builders.com/backend/v1
LLM_BINDING_API_KEY=your_api_key
LLM_MODEL=deepseek  # 或其他模型

# === Neo4j 配置 ===
USE_NEO4J=true
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_MAX_POOL_SIZE=50
NEO4J_BATCH_SIZE=500

# === 处理配置 ===
CONCURRENT_REQUESTS=5  # 并发 LLM 请求数
MAX_RETRIES=3
CHUNK_SIZE=800
CHUNK_OVERLAP_RATIO=0.5

# === 可观测性（可选）===
# Langfuse
LANGFUSE_ENABLED=false
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=https://cloud.langfuse.com

# Phoenix
PHOENIX_ENABLED=false
PHOENIX_ENDPOINT=http://localhost:6006/v1/traces

# === 服务配置 ===
HOST=0.0.0.0
PORT=9621
```

### 故障排查

**Neo4j 连接失败**
```bash
# 检查 Neo4j 是否运行
docker ps | grep neo4j

# 查看日志
docker logs neo4j

# 确认 .env 中的凭据与 Neo4j 设置匹配
```

**API 服务器无法启动**
```bash
# 检查端口是否可用
lsof -i :9621

# 查看日志获取详细错误信息
python -m backend.server
```

**文档处理卡住**
```bash
# 检查进度
curl "http://localhost:9621/documents/progress/YOUR_DOC_ID"

# 检查检查点文件
ls -la data/checkpoints/YOUR_DOC_ID/

# 重新处理（将从检查点继续）
curl -X POST "http://localhost:9621/documents/upload-async" \
  -F "file=@same_document.txt"
```

**LLM API 错误**
```bash
# 验证 API 密钥是否正确
# 检查 LLM_BINDING_HOST 是否可访问
# 查看速率限制和配额
```

更多详细指南，请参考[文档索引](docs/README.md)。

## 项目结构

```
KnowledgeWeaver/
├── backend/              # 后端代码
│   ├── server.py        # FastAPI 服务
│   ├── extractor.py     # 知识提取
│   ├── hybrid_retriever.py  # 混合检索器
│   ├── qa_engine.py     # 问答引擎
│   ├── vector_store.py  # 向量存储
│   ├── embedder.py      # 文本嵌入
│   └── prompts/         # 提示词模板
├── frontend/            # 前端代码
│   ├── kg-config.js     # 图谱配置
│   └── kg-normalizer.js # 图谱规范化
├── data/                # 数据目录（gitignored）
│   ├── storage/         # 持久化存储
│   │   └── vector_db/   # 向量数据库（ChromaDB）
│   ├── checkpoints/     # 处理检查点（支持断点续传）
│   ├── progress/        # 进度追踪数据
│   └── inputs/          # 用户上传文件
├── docs/                # 文档
│   ├── architecture/    # 架构图和设计文档
│   ├── deployment/      # AWS 和部署指南
│   ├── database/        # 数据库设置和优化指南
│   ├── observability/   # 监控和可观测性文档
│   ├── development/     # 开发和测试指南
│   ├── security/        # 安全最佳实践和指南
│   └── README.md        # 文档索引
└── tests/               # 测试用例
```

## 主要特性

### 知识图谱规范化
- 实体去重和合并
- 关系标准化
- 信息孤岛检测和连接

### 混合检索策略
- 向量相似度检索（RAG）
- 图谱结构检索（KG）
- 动态权重融合

### 智能问答
- 上下文感知
- 多源信息整合
- 结构化答案生成

## 许可证

MIT License
