# KnowledgeWeaver 项目结构回顾

## 📊 项目概览

**项目名称：** KnowledgeWeaver
**版本：** 2.0.0
**架构：** 模块化单体应用（Backend API + Frontend）
**最后更新：** 2026-01-26

## 🏗️ 整体架构

```
KnowledgeWeaver/
├── backend/              # 后端服务（Python/FastAPI）
├── frontend/             # 前端界面（HTML/JS/D3.js）
├── tests/                # 测试套件
├── docs/                 # 文档
├── data/                 # 运行时数据
├── scripts/              # 工具脚本
├── docker/               # Docker 配置
└── tools/                # 开发工具
```

## 📁 详细目录结构

### 1. Backend（后端服务）

```
backend/
├── core/                           # 核心模块
│   ├── config.py                   # 配置和提示词模板
│   ├── observability.py            # Langfuse 可观测性
│   ├── phoenix_observability.py    # Phoenix 可观测性
│   ├── embeddings/                 # 嵌入服务
│   │   ├── __init__.py
│   │   └── service.py              # OpenAI 兼容嵌入服务
│   └── storage/                    # 存储层
│       ├── __init__.py
│       ├── neo4j.py                # Neo4j 图存储
│       └── vector.py               # ChromaDB 向量存储
│
├── extraction/                     # 知识提取模块
│   ├── __init__.py
│   ├── extractor.py                # 同步提取器
│   ├── async_extractor.py          # 异步提取器（Claude CLI）
│   ├── normalizer.py               # 图谱规范化
│   └── entity_filter.py            # 实体过滤
│
├── retrieval/                      # 检索模块
│   ├── __init__.py
│   ├── hybrid_retriever.py         # 混合检索器（KG + RAG）
│   ├── qa_engine.py                # 问答引擎
│   └── prompts/                    # 提示词管理
│       ├── __init__.py
│       ├── prompt_loader.py        # 提示词加载器
│       ├── extraction_prompts.py   # 提取提示词
│       ├── qa_prompts.py           # 问答提示词
│       ├── extraction.md           # 提取提示词模板
│       ├── document_topic.md       # 文档主题提示词
│       └── README.md               # 提示词文档
│
├── management/                     # 管理模块
│   ├── __init__.py
│   ├── kg_manager.py               # 知识图谱统一管理
│   └── progress_tracker.py         # 进度追踪
│
├── data/                           # 后端数据（遗留，应移除）
│   ├── checkpoints/                # ⚠️ 遗留目录
│   ├── progress/                   # ⚠️ 遗留目录
│   └── storage/                    # ⚠️ 遗留目录
│
├── server.py                       # FastAPI 服务入口
├── process_book.py                 # 文档处理脚本
├── prompt_manager.py               # 提示词管理器（遗留）
├── test_imports.py                 # 导入测试
└── TEST_REPORT.md                  # 测试报告
```

#### Backend 模块说明

| 模块 | 职责 | 关键文件 |
|------|------|---------|
| `core/` | 核心功能和配置 | config.py, embeddings, storage |
| `extraction/` | 知识图谱提取 | extractor.py, normalizer.py |
| `retrieval/` | 检索和问答 | hybrid_retriever.py, qa_engine.py |
| `management/` | 图谱管理和进度追踪 | kg_manager.py, progress_tracker.py |

### 2. Frontend（前端界面）

```
frontend/
├── index.html           # 主页面
├── kg-*.js              # 知识图谱可视化脚本
└── graph.js             # 图谱交互逻辑
```

### 3. Tests（测试套件）

```
tests/
├── conftest.py                  # Pytest 配置和 fixtures ✅
├── pytest.ini                   # Pytest 配置文件 ✅
├── README.md                    # 测试文档 ✅
│
├── test_config.py               # 配置模块测试 (12 tests) ✅
├── test_normalizer.py           # 规范化器测试 (19 tests) ✅
├── test_entity_filter.py        # 实体过滤测试 (12 tests) ✅
├── test_embeddings.py           # 嵌入服务测试 (11 tests) ✅
├── test_kg_manager.py           # KG 管理器测试 (15 tests) ✅
├── test_progress_tracker.py     # 进度追踪测试 (10 tests) ✅
├── test_api.py                  # API 端点测试 (13 tests) ✅
│
├── test_langfuse_connection.py  # Langfuse 连接测试
├── test_langfuse_openai.py      # Langfuse OpenAI 集成测试
│
├── data/                        # 测试数据
│   ├── __enqueued__/
│   ├── test_small.txt
│   └── 让时间陪你慢慢变富.txt
│
└── e2e/                         # 端到端测试（待添加）
```

**测试统计：**
- ✅ 92 个测试用例
- ✅ 94% 通过率
- ✅ 覆盖 7 个核心模块

### 4. Docs（文档）

```
docs/
├── README.md                      # 文档索引
├── TEST_SUITE.md                  # 测试套件文档 ✅
├── NEO4J_GUIDE.md                 # Neo4j 使用指南
├── LANGFUSE_GUIDE.md              # Langfuse 完整指南
├── PHOENIX_INTEGRATION.md         # Phoenix 集成文档
├── OBSERVABILITY_COMPARISON.md    # 可观测性方案对比
├── OBSERVABILITY_WORKFLOW.md      # 可观测性工作流
├── TEST_LANGFUSE.md               # Langfuse 测试文档
└── PROJECT_STRUCTURE.md           # 本文件 ✅
```

### 5. Data（运行时数据）

```
data/
├── storage/                     # 持久化存储
│   ├── graphs/                  # 图谱数据（JSON）
│   ├── graphs_backup/           # 图谱备份
│   ├── vector_db/               # ChromaDB 向量数据库
│   └── rag/                     # RAG 相关数据
│
├── inputs/                      # 上传文件
│   └── __enqueued__/            # 待处理文件队列
│
├── checkpoints/                 # 断点续传数据
├── progress/                    # 进度追踪数据
└── cache/                       # 缓存数据
```

⚠️ **注意：** `data/` 目录在 `.gitignore` 中，不应提交到版本控制。

### 6. Scripts（工具脚本）

```
scripts/
├── migrate_data_structure.sh   # 数据结构迁移
├── start_phoenix.sh            # 启动 Phoenix
└── test_upload.sh              # 测试上传
```

### 7. 部署配置（Deployment）

```
deploy/
├── docker/                      # Docker 镜像构建
│   └── api/
│       ├── Dockerfile           # API 服务镜像
│       └── .dockerignore        # Docker 构建忽略文件
├── kubernetes/                  # Kubernetes 配置
│   ├── base/                    # 基础配置
│   │   ├── kustomization.yaml
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   └── overlays/                # 环境特定配置
│       ├── dev/                 # 开发环境
│       ├── staging/             # 预发布环境
│       └── production/          # 生产环境
└── terraform/                   # AWS 基础设施即代码
    ├── main.tf                  # EKS 集群配置
    ├── variables.tf             # 变量定义
    └── outputs.tf               # 输出配置
```

📌 **注意**：项目已迁移到 Kubernetes 部署，不再使用 Docker Compose。

### 8. Tools（开发工具）

```
tools/
├── code_checker.py              # 代码检查工具
└── hooks/                       # Git hooks（待添加）
```

### 9. 配置文件

```
根目录/
├── .env                         # 环境变量（不提交）
├── .env.example                 # 环境变量示例
├── .gitignore                   # Git 忽略规则
├── .codecheck.json              # 代码检查配置
├── requirements.txt             # Python 依赖
├── CLAUDE.md                    # Claude 项目配置
├── README.md                    # 项目说明（英文）
├── README_CN.md                 # 项目说明（中文）
├── TEST_SUMMARY.md              # 测试总结 ✅
└── run_tests.sh                 # 测试运行脚本 ✅
```

## 📊 代码统计

### 代码行数

```bash
# Python 代码
backend/: ~3500 行
tests/: ~1800 行

# 文档
docs/: ~2000 行
README: ~500 行

# 配置
配置文件: ~200 行
```

### 文件数量

| 类型 | 数量 |
|------|------|
| Python 文件 (.py) | 42 |
| 文档 (.md) | 16 |
| 配置文件 | 8 |
| 测试文件 | 10 |
| 脚本 (.sh) | 4 |

## 🔍 问题和改进建议

### 1. ⚠️ 重复目录结构

**问题：**
```
backend/data/          # ❌ 遗留目录，应删除
data/                  # ✅ 正确的数据目录
```

**建议：**
- 删除 `backend/data/` 目录
- 所有数据统一存放在项目根目录的 `data/`
- 更新代码中的路径引用

### 2. ⚠️ 敏感信息问题

**注意：**
Kubernetes 部署中的敏感信息管理：
- 使用 Kubernetes Secrets 存储敏感数据
- 不要在配置文件中硬编码密码
- 使用 AWS Secrets Manager 或参数存储

**最佳实践：**
```yaml
# Kubernetes Secret 示例
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  database-url: <base64-encoded>
  api-key: <base64-encoded>
```

### 4. 📝 测试数据管理

**问题：**
```
data/inputs/__enqueued__/          # 包含大量测试文件（20+ 个）
tests/data/                        # 测试数据
```

**建议：**
- 清理 `data/inputs/__enqueued__/` 中的旧文件
- 测试数据统一放在 `tests/data/`
- 添加数据清理脚本

### 5. 🔧 配置文件优化

**问题：**
- `.env.example` 不存在
- 配置分散在多个文件

**建议：**
创建 `.env.example`：
```bash
# LLM 配置
LLM_BINDING_HOST=https://space.ai-builders.com/backend/v1
LLM_BINDING_API_KEY=your_api_key_here
LLM_MODEL=deepseek
EMBEDDING_MODEL=text-embedding-ada-002

# Neo4j 配置
USE_NEO4J=true
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here

# Langfuse 配置
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key
LANGFUSE_HOST=http://localhost:3000

# 服务配置
HOST=0.0.0.0
PORT=9621
```

### 6. 📚 文档组织

**当前状态：** ✅ 良好

**文档列表：**
- ✅ 测试文档完善
- ✅ Neo4j 指南
- ✅ Langfuse 指南
- ✅ Phoenix 集成
- ✅ 可观测性对比

**建议：**
- ✅ 创建文档索引（已有 docs/README.md）
- 🔄 添加 API 文档（OpenAPI/Swagger）
- 🔄 添加部署文档

### 7. 🧪 测试覆盖

**当前状态：** ✅ 优秀（94% 通过率）

**已覆盖：**
- ✅ 配置模块（100%）
- ✅ 规范化器（100%）
- ✅ 实体过滤（100%）
- ✅ 进度追踪（100%）
- ✅ 嵌入服务（91%）
- ✅ KG 管理器（73%）
- ✅ API 端点（92%）

**待添加：**
- 🔄 知识提取器测试
- 🔄 异步提取器测试
- 🔄 混合检索器测试
- 🔄 问答引擎测试
- 🔄 Neo4j 存储测试
- 🔄 端到端测试

## 🎯 模块依赖关系

```
server.py (FastAPI)
    ├── management/
    │   ├── kg_manager.py
    │   │   ├── storage/neo4j.py
    │   │   └── extraction/normalizer.py
    │   └── progress_tracker.py
    │
    ├── extraction/
    │   ├── async_extractor.py
    │   │   ├── normalizer.py
    │   │   └── entity_filter.py
    │   └── extractor.py
    │
    ├── retrieval/
    │   ├── qa_engine.py
    │   │   └── hybrid_retriever.py
    │   └── prompts/
    │
    ├── core/
    │   ├── storage/
    │   │   ├── neo4j.py
    │   │   └── vector.py
    │   ├── embeddings/service.py
    │   └── observability.py
    │
    └── frontend/
```

## 📦 依赖管理

### Python 依赖（requirements.txt）

```
# Web 框架
fastapi>=0.104.0
uvicorn>=0.24.0

# AI/ML
openai>=1.0.0
google-genai>=0.1.0

# 数据库
neo4j>=5.0.0
chromadb>=0.4.0

# 可观测性
langfuse>=2.0.0

# 测试
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
httpx>=0.24.0

# 工具
python-dotenv>=1.0.0
python-multipart>=0.0.6
tqdm>=4.65.0
```

## 🚀 部署架构

### 开发环境

```
本地开发
├── Python 3.9+
├── Neo4j（Docker 或本地）
├── ChromaDB（本地）
└── Langfuse（可选，Docker）
```

### 生产环境（推荐）

```
生产部署
├── Backend（FastAPI）
│   ├── Gunicorn/Uvicorn
│   └── 多进程/多线程
│
├── 数据库
│   ├── Neo4j Cluster
│   └── PostgreSQL（Langfuse）
│
├── 存储
│   ├── ChromaDB（持久化）
│   └── 文件存储（S3/OSS）
│
└── 监控
    └── Langfuse/Phoenix
```

## 🔄 数据流

### 文档处理流程

```
1. 上传文档
   ↓
2. 文件保存（data/inputs/__enqueued__/）
   ↓
3. 异步提取（async_extractor.py）
   ├── 分块
   ├── 并发调用 Claude CLI
   ├── 提取实体和关系
   └── 规范化
   ↓
4. 存储
   ├── Neo4j（图谱）
   └── ChromaDB（向量）
   ↓
5. 完成（更新进度）
```

### 问答流程

```
1. 用户提问
   ↓
2. 混合检索
   ├── 图谱检索（Neo4j）
   └── 向量检索（ChromaDB）
   ↓
3. 上下文整合
   ↓
4. LLM 生成答案
   ↓
5. 返回结果（附带来源）
```

## 📈 性能指标

### 当前性能

| 指标 | 数值 |
|------|------|
| 文档处理速度 | 1.5-2 分钟（160KB，并发5） |
| 并发提取 | 3-5 倍提升（vs 串行） |
| 测试通过率 | 94% |
| 代码覆盖率 | ~75% |
| API 响应时间 | < 100ms（健康检查） |

### 优化建议

1. **缓存优化**
   - 嵌入结果缓存
   - LLM 响应缓存
   - 图谱查询缓存

2. **并发优化**
   - 提高并发数（当前 5）
   - 使用连接池
   - 批量操作

3. **数据库优化**
   - Neo4j 索引优化
   - ChromaDB 批量插入
   - 定期清理旧数据

## 🔐 安全性

### 当前状态

✅ **已实现：**
- 环境变量管理
- `.gitignore` 配置
- Git hooks（敏感信息检测）

⚠️ **待改进：**
- Kubernetes Secrets 管理
- API 认证/授权
- 速率限制
- 输入验证

### 安全检查清单

- [x] 移除 Docker Compose（已迁移到 Kubernetes）
- [ ] 配置 Kubernetes Secrets
- [ ] 创建 `.env.example`
- [ ] 添加 API 认证
- [ ] 实现速率限制
- [ ] 添加输入验证和清理
- [ ] 配置 CORS 白名单
- [ ] 启用 HTTPS（生产环境）
- [ ] 配置 AWS IAM 角色和策略

## 📝 维护建议

### 定期任务

1. **每周**
   - 清理测试数据
   - 检查日志文件大小
   - 更新依赖包

2. **每月**
   - 备份 Neo4j 数据
   - 清理向量数据库
   - 性能分析

3. **每季度**
   - 代码审查
   - 安全审计
   - 架构评估

### 代码质量

```bash
# 运行测试
./run_tests.sh

# 生成覆盖率报告
./run_tests.sh coverage

# 代码检查
python tools/code_checker.py

# 格式化代码
black backend/ tests/

# 类型检查
mypy backend/
```

## 📞 联系方式

- **维护者：** Sheldon
- **项目：** KnowledgeWeaver
- **版本：** 2.0.0
- **最后更新：** 2026-01-26

---

## 附录：快速参考

### 常用命令

```bash
# 本地开发 - 直接运行
cd backend && python server.py

# 本地开发 - Kubernetes
kubectl apply -k deploy/kubernetes/overlays/dev

# 生产部署 - AWS EKS
kubectl apply -k deploy/kubernetes/overlays/production

# 运行测试
pytest
./run_tests.sh

# 查看 Kubernetes 资源
kubectl get pods
kubectl get services
kubectl logs -f <pod-name>

# 数据迁移
./scripts/migrate_data_structure.sh
```

### 目录快速访问

```bash
# 查看日志
tail -f logs/*.log

# 清理数据
rm -rf data/storage/*
rm -rf data/cache/*

# 备份数据
tar -czf backup.tar.gz data/storage/

# 查看进度
cat data/progress/*.json
```
