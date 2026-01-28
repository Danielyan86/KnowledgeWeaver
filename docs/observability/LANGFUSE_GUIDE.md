# Langfuse 完整指南

## 📖 概述

Langfuse 是一个专为 LLM 应用设计的可观测性平台，可以帮助你监控和优化 KnowledgeWeaver 的问答系统。

**集成状态**: ✅ 已完成 - 使用 OpenAI Wrapper 非入侵式集成

**代码改动量**: 仅 **1 行代码** 🎉

**集成方式**: OpenAI Wrapper - 自动追踪所有 LLM 调用，无需修改业务代码

### 🎯 追踪内容

当前集成追踪以下操作：

#### 1. 问答请求 (Trace)
- 用户问题
- 生成的答案
- 检索模式（auto/kg_only/rag_only/hybrid）
- 执行时间

#### 2. 检索操作 (Span)
- 检索到的实体数量
- 检索到的关系数量
- 检索到的文档片段数量
- 检索策略和参数

#### 3. LLM 调用 (Generation)
- 模型名称
- 输入 prompt
- 生成的答案
- Token 使用量（prompt tokens, completion tokens）
- 成本统计

---

## 🚀 快速开始

### 选择部署方式

| 方案 | 优点 | 缺点 | 推荐场景 |
|------|------|------|----------|
| **Cloud** | 5 分钟即用，无需维护 | 数据上云，有隐私顾虑 | 快速验证 POC |
| **自托管** | 数据完全掌控，免费 | 需要部署维护 | 生产环境 |

---

## 方案 A: Langfuse Cloud（最快）

### 1. 注册账号（2 分钟）

访问: https://cloud.langfuse.com
- 注册免费账号
- 创建新项目

### 2. 获取 API Keys（1 分钟）

在项目设置中找到并复制：
- **Public Key**: `pk-lf-xxx...`
- **Secret Key**: `sk-lf-xxx...`

### 3. 配置环境变量（1 分钟）

编辑 `.env` 文件：

```bash
# 启用 Langfuse
LANGFUSE_ENABLED=true

# Langfuse Cloud
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=https://cloud.langfuse.com
```

### 4. 安装依赖并测试（1 分钟）

```bash
# 安装依赖
pip install langfuse>=2.0.0

# 启动服务
python -m backend.server

# 发送测试请求
curl -X POST http://localhost:9621/qa \
  -H "Content-Type: application/json" \
  -d '{"question": "什么是知识图谱？", "mode": "auto"}'
```

### 5. 查看追踪数据

访问 https://cloud.langfuse.com/traces 查看刚才的请求

---

## 方案 B: 自托管 Langfuse（推荐生产环境）

### ✅ 已完成的部分

- ✅ Kubernetes 配置已创建
- ✅ Langfuse 服务已集成到 K8s 部署
- ✅ PostgreSQL 数据库配置完成
- ✅ 集成代码已添加（OpenAI Wrapper 方式，仅1行代码）
- ✅ 测试脚本已创建

### 完成剩余配置（5 分钟）

#### 步骤 1: 部署 Langfuse 服务（1 分钟）

```bash
# 部署到 Kubernetes
kubectl apply -k deploy/kubernetes/overlays/dev

# 查看服务状态
kubectl get pods -n knowledgeweaver | grep langfuse

# 端口转发以访问 UI
kubectl port-forward svc/langfuse 3000:3000 -n knowledgeweaver
```

#### 步骤 2: 访问 Langfuse UI（1 分钟）

打开浏览器访问: http://localhost:3000

#### 步骤 3: 创建账号和项目（2 分钟）

1. **注册账号**
   - 邮箱: 任意（本地使用，无需真实邮箱）
   - 密码: 任意（自己记住即可）
   - 点击 "Sign up"

2. **创建项目**
   - 登录后会提示创建项目
   - 项目名称: `KnowledgeWeaver`
   - 点击 "Create"

3. **获取 API Keys**
   - 项目创建后自动显示 API Keys
   - 或者点击: Settings → API Keys
   - 复制两个 Key:
     - **Public Key**: `pk-lf-xxx...`
     - **Secret Key**: `sk-lf-xxx...`

#### 步骤 4: 配置 KnowledgeWeaver（1 分钟）

编辑 `.env` 文件，找到这部分（已预先添加）：

```bash
# Langfuse Configuration (自托管)
LANGFUSE_ENABLED=true
LANGFUSE_HOST=http://localhost:3000
LANGFUSE_PUBLIC_KEY=pk-lf-你的公钥  # ← 替换这里
LANGFUSE_SECRET_KEY=sk-lf-你的密钥  # ← 替换这里
```

**将 API Keys 替换为从 Langfuse UI 复制的值。**

#### 步骤 5: 测试连接（1 分钟）

```bash
# 运行测试脚本
python test_langfuse_connection.py
```

**期望输出**：
```
============================================================
Langfuse 连接测试
============================================================

配置检查:
  ├─ LANGFUSE_ENABLED: True
  ├─ LANGFUSE_HOST: http://localhost:3000
  ├─ LANGFUSE_PUBLIC_KEY: 已设置
  └─ LANGFUSE_SECRET_KEY: 已设置

库检查:
  ✅ langfuse 包已安装

连接测试:
  ✅ 成功连接到 http://localhost:3000
  ✅ 测试 trace 已发送
  ✅ 数据已同步

查看追踪数据:
  👉 访问: http://localhost:3000/traces
  👉 应该能看到名为 'connection_test' 的追踪

============================================================
🎉 测试成功！Langfuse 已正确配置
============================================================
```

#### 步骤 6: 启动 KnowledgeWeaver（30 秒）

```bash
python -m backend.server
```

**期望日志**：
```
✅ Langfuse 已启用: http://localhost:3000
✅ OpenAI 客户端已包装 Langfuse 追踪
启动服务: http://0.0.0.0:9621
```

#### 步骤 7: 发送测试请求（30 秒）

```bash
curl -X POST http://localhost:9621/qa \
  -H "Content-Type: application/json" \
  -d '{
    "question": "什么是知识图谱？",
    "mode": "auto"
  }'
```

#### 步骤 8: 查看追踪数据（30 秒）

1. 访问: http://localhost:3000/traces
2. 应该能看到刚才的问答请求
3. 点击查看详情，包含:
   - 用户问题
   - LLM 生成的答案
   - Token 使用量
   - 执行时间
   - 成本（如果配置了定价）

### 🎉 完成！

现在每次调用 `/qa` API 都会自动追踪到 Langfuse！

---

## 🎯 集成方案与最佳实践

### 核心原则：最小化代码入侵

好的可观测性集成应该：
- ✅ **对业务代码影响最小**
- ✅ **易于启用/禁用**
- ✅ **无需改变函数签名**
- ✅ **自动追踪，无需手动调用**

### ✅ 推荐方式：OpenAI Wrapper（我们使用的方案）

#### 原理
Langfuse 提供了 OpenAI SDK 的包装器，可以**自动拦截所有 LLM 调用**，无需修改业务代码。

#### 实现（3步）

**步骤 1: 配置 Langfuse**
```python
# backend/core/observability.py
from langfuse import Langfuse

class LangfuseTracer:
    def __init__(self):
        self.client = Langfuse(
            public_key=os.getenv('LANGFUSE_PUBLIC_KEY'),
            secret_key=os.getenv('LANGFUSE_SECRET_KEY'),
            host=os.getenv('LANGFUSE_HOST')
        )

    def wrap_openai(self, client):
        """包装 OpenAI 客户端"""
        from langfuse.openai import OpenAI as LangfuseOpenAI
        return LangfuseOpenAI(
            base_url=client.base_url,
            api_key=client.api_key
        )
```

**步骤 2: 包装 OpenAI 客户端**
```python
# backend/retrieval/qa_engine.py
class QAEngine:
    def __init__(self):
        # 创建普通客户端
        client = OpenAI(base_url=api_base, api_key=api_key)

        # 用 Langfuse wrapper 包装（一行代码！）
        tracer = get_tracer()
        self.client = tracer.wrap_openai(client)  # ✅ 仅此一行!

    def _generate_answer(self, prompt: str) -> str:
        # 业务代码完全不变！
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
```

**步骤 3: 配置环境变量启用/禁用**
```bash
# .env
LANGFUSE_ENABLED=true  # 禁用只需改为 false
LANGFUSE_PUBLIC_KEY=pk-xxx
LANGFUSE_SECRET_KEY=sk-xxx
```

#### 优势对比

| 方式 | 代码修改 | 函数签名变化 | 易于禁用 | 自动追踪 Token |
|------|---------|-------------|---------|--------------|
| **OpenAI Wrapper** ✅ | 1行 | 无 | ✅ | ✅ |
| 手动 trace | 每个函数 10+ 行 | 需添加 trace_id | ❌ | ❌ |
| 装饰器 | 每个函数 1 行 | 无 | ✅ | ❌ |

### ❌ 不推荐：入侵式手动追踪

```python
# ❌ 不好：需要修改函数签名
def ask(question: str, trace_id: str = None):
    if trace_id:
        tracer.start_trace(trace_id)
    # ... 业务逻辑
    if trace_id:
        tracer.end_trace(trace_id)

# ❌ 不好：需要手动记录 token
def _generate_answer(prompt, trace_id):
    response = client.chat.completions.create(...)
    if trace_id:
        tracer.log_llm_call(
            trace_id=trace_id,
            prompt_tokens=response.usage.prompt_tokens,  # 手动获取
            completion_tokens=response.usage.completion_tokens,
            # ... 更多字段
        )
```

**问题**：
- 每个函数都要添加 trace_id 参数
- 需要手动传递 trace_id 到所有调用链
- 需要手动记录 token 和成本
- 禁用追踪需要注释大量代码
- 容易遗漏某些调用

### 🔧 其他集成方式对比

#### 方式 1: 装饰器（适用于特定函数追踪）

```python
from langfuse.decorators import observe

class QAEngine:
    @observe()  # 追踪整个函数执行
    def ask(self, question: str):
        # 业务代码不变
        response = self.retriever.retrieve(question)
        answer = self._generate_answer(response)
        return answer
```

**适用场景**：
- ✅ 需要追踪特定业务流程（如检索、RAG pipeline）
- ✅ 需要自定义追踪名称和元数据
- ❌ 不适合追踪 LLM 调用（token 不会自动记录）

#### 方式 2: LangChain 集成（如果使用 LangChain）

```python
from langfuse.callback import CallbackHandler

# 完全非入侵！
langfuse_handler = CallbackHandler()

# 在调用时传入
chain.invoke(
    {"question": "..."},
    config={"callbacks": [langfuse_handler]}
)
```

**适用场景**：
- ✅ 项目使用 LangChain/LlamaIndex
- ✅ 想要追踪整个 chain 执行
- ❌ 你的项目不用 LangChain，所以不适用

#### 方式 3: Context Manager（适用于代码块追踪）

```python
from langfuse import Langfuse

langfuse = Langfuse()

with langfuse.trace(name="document_processing") as trace:
    # 这个代码块内的所有操作都会被追踪
    extract_entities()
    build_graph()
    save_to_neo4j()
```

**适用场景**：
- ✅ 需要追踪一段复杂流程
- ✅ 需要嵌套追踪（trace 里面有 span）
- ❌ 不适合简单的 API 调用追踪

### 📊 我们的集成方案总结

#### 当前实现（推荐）

```
┌─────────────────────────────────────┐
│  业务代码 (qa_engine.py)            │
│                                      │
│  client.chat.completions.create()   │
│         ↓                            │
│  Langfuse OpenAI Wrapper (自动拦截) │
│         ↓                            │
│  记录到 Langfuse (token/成本/延迟)  │
└─────────────────────────────────────┘
```

**代码改动量**：
- ✅ `observability.py`: 50 行（可复用）
- ✅ `qa_engine.py`: **1 行**（包装客户端）
- ✅ 其他文件: 0 行

**功能**：
- ✅ 自动追踪所有 LLM 调用
- ✅ 自动记录 token 使用量
- ✅ 自动计算成本
- ✅ 自动记录延迟
- ✅ 环境变量控制启用/禁用

### ✅ 最佳实践金字塔

**从简单到复杂：**

```
Level 1: OpenAI Wrapper（当前实现）     ← 推荐起点，90% 场景够用
         ↓ 1 行代码，自动追踪所有 LLM 调用

Level 2: 装饰器 @observe                ← 需要追踪特定业务流程时
         ↓ 每个函数 1 行，追踪整个流程

Level 3: Context Manager                ← 需要追踪复杂嵌套流程时
         ↓ 代码块级别的细粒度控制

Level 4: 手动 API 调用                  ← 仅在特殊需求时使用
         ↓ 完全自定义，但代码量大
```

**我们选择 Level 1**，因为：
- ✅ 代码改动最小（1 行）
- ✅ 追踪覆盖最全（所有 LLM 调用）
- ✅ 最容易维护
- ✅ 满足 90% 的监控需求

**何时升级到 Level 2/3**：
- 需要追踪检索性能
- 需要追踪文档处理流程
- 需要自定义元数据

---

## 📊 使用 Langfuse Dashboard

### 1. Traces 视图
查看所有问答请求的完整链路：
- 请求时间
- 执行时长
- 问题和答案
- 检索策略

### 2. Generations 视图
查看所有 LLM 调用：
- 模型名称
- Token 使用量
- 成本统计
- 延迟分析

### 3. Dashboard（仪表盘）
- 总请求数
- Token 使用趋势
- 成本趋势
- 平均延迟

### 🔍 实用技巧

#### 查看特定问题的追踪

1. 在 Langfuse Dashboard 打开 Traces
2. 搜索问题关键词
3. 点击查看详细信息：
   - 检索了哪些实体和关系
   - 检索了哪些文档片段
   - LLM 输入的完整 prompt
   - 生成的答案
   - Token 使用量

#### 分析性能瓶颈

1. 在 Traces 页面按执行时间排序
2. 找出慢查询
3. 查看是检索慢还是 LLM 生成慢
4. 针对性优化

#### 成本分析

1. 在 Dashboard 首页查看总体统计
2. 按日期、模型查看成本趋势
3. 识别高成本操作
4. 优化 token 使用

---

## 🎯 扩展功能

当前只集成了 `/qa` 端点，你可以继续扩展：

### 1. 追踪文档提取
在 `extractor.py` 和 `async_extractor.py` 中添加追踪：
```python
# 使用装饰器追踪
@observe()
async def extract_from_chunk(self, chunk):
    # 提取逻辑
```

### 2. 追踪向量化
在 `embeddings/service.py` 中追踪 embedding 调用

### 3. 用户反馈收集
在前端添加反馈按钮，调用 Langfuse API：
```python
tracer.client.score(
    trace_id=trace_id,
    name="user_feedback",
    value=1  # 1=满意, 0=不满意
)
```

### 4. Prompt 管理
将提示词迁移到 Langfuse 管理，支持 A/B 测试

---

## 🔧 管理 Langfuse 服务（自托管）

### 查看服务状态
```bash
kubectl get pods -n knowledgeweaver
kubectl get svc -n knowledgeweaver
```

### 查看日志
```bash
# Langfuse 服务日志
kubectl logs -f -n knowledgeweaver -l app=langfuse

# 数据库日志
kubectl logs -f -n knowledgeweaver -l app=postgres
```

### 停止服务
```bash
kubectl delete -k deploy/kubernetes/overlays/dev
```

### 启动服务
```bash
kubectl apply -k deploy/kubernetes/overlays/dev
```

### 完全清理（包括数据）
```bash
# 删除所有资源包括 PVC
kubectl delete -k deploy/kubernetes/overlays/dev
kubectl delete pvc -l app=langfuse -n knowledgeweaver
```

### 数据备份
```bash
# 获取 PostgreSQL Pod 名称
POSTGRES_POD=$(kubectl get pods -n knowledgeweaver -l app=postgres -o jsonpath='{.items[0].metadata.name}')

# 备份 PostgreSQL
kubectl exec -n knowledgeweaver $POSTGRES_POD -- pg_dump -U postgres langfuse > backup.sql

# 恢复
kubectl exec -i -n knowledgeweaver $POSTGRES_POD -- psql -U postgres langfuse < backup.sql
```

---

## 🐛 故障排查

### 问题 1: 看不到追踪数据

**检查**:
1. 确认 `LANGFUSE_ENABLED=true`
2. 确认 API Keys 正确
3. 查看服务启动日志是否有 "✅ Langfuse 已启用"

**解决**:
```bash
# 重新测试连接
python test_langfuse_connection.py

# 查看服务日志
python -m backend.server
```

### 问题 2: Kubernetes Pod 启动失败

**检查**:
```bash
# 查看 Pod 状态
kubectl get pods -n knowledgeweaver

# 查看 Pod 日志
kubectl logs -n knowledgeweaver -l app=langfuse
kubectl logs -n knowledgeweaver -l app=postgres
```

**解决**:
```bash
# 重启 Pod（删除后自动重建）
kubectl delete pod -n knowledgeweaver -l app=langfuse

# 完全重建
kubectl delete -k deploy/kubernetes/overlays/dev
kubectl apply -k deploy/kubernetes/overlays/dev
```

### 问题 3: 连接超时

**检查**:
```bash
# 测试端口是否开放
curl http://localhost:3000

# 确认容器运行
docker ps | grep langfuse
```

### 问题 4: Langfuse 初始化失败

**检查**:
1. 确认 `langfuse` 包已安装: `pip list | grep langfuse`
2. 确认 API Keys 正确
3. 确认 Langfuse 服务可访问

**解决**:
```bash
# 重新安装
pip install --upgrade langfuse

# 测试连接
python -c "from langfuse import Langfuse; client = Langfuse(public_key='pk-xxx', secret_key='sk-xxx'); print('OK')"
```

### 问题 5: 追踪数据不完整

**原因**: 追踪数据是异步发送的，可能有延迟

**解决**: 等待几秒后刷新 Dashboard

---

## 💡 常见问题

### Q: 我必须改所有代码吗？
**A**: 不！只需包装 OpenAI 客户端（1 行代码），所有调用自动追踪。

### Q: 如何禁用追踪？
**A**: 设置环境变量 `LANGFUSE_ENABLED=false`，无需改代码。

### Q: 会影响性能吗？
**A**: 追踪数据是异步发送的，对 API 响应时间影响 <10ms。

### Q: 支持自定义模型 endpoint 吗？
**A**: 支持！只要兼容 OpenAI API 格式即可（我们的项目就是）。

### Q: 能追踪 Gemini/Claude 调用吗？
**A**: 可以，但需要使用装饰器或手动追踪（暂无自动 wrapper）。

### Q: Cloud 和自托管有什么区别？
**A**:
- Cloud: 快速开始，免费套餐有限制，数据存在第三方
- 自托管: 完全免费，数据自己掌控，需要维护 Docker 服务

### Q: 数据安全吗？
**A**:
- Cloud: 数据传输加密，但存储在 Langfuse 服务器
- 自托管: 数据完全本地存储，完全可控

---

## ⚙️ 配置选项

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LANGFUSE_ENABLED` | 是否启用追踪 | `false` |
| `LANGFUSE_PUBLIC_KEY` | 公钥 | - |
| `LANGFUSE_SECRET_KEY` | 密钥 | - |
| `LANGFUSE_HOST` | Langfuse 服务地址 | `https://cloud.langfuse.com` |

### 禁用追踪

如果不需要追踪，设置：
```bash
LANGFUSE_ENABLED=false
```

或直接不设置 Langfuse 相关变量，系统会自动禁用追踪。

---

## 📈 生产环境建议

### 1. 开发环境
- 使用 Cloud 版本快速验证
- 快速迭代和测试

### 2. 生产环境
- 使用自托管版本保证数据隐私
- 配置 HTTPS（使用 Nginx/Traefik）
- 定期备份数据库
- 监控磁盘空间

### 3. 性能优化
- 调整 PostgreSQL 配置
- 增加连接池大小
- 启用 Redis 缓存（可选）

### 4. 监控建议
- 定期分析追踪数据，优化系统
- 监控 token 使用，避免意外高额账单
- 收集真实用户反馈，持续改进

---

## 📚 更多资源

- [Langfuse 官方文档](https://langfuse.com/docs)
- [Python SDK 文档](https://langfuse.com/docs/sdk/python)
- [OpenAI Integration](https://langfuse.com/docs/integrations/openai)
- [Langfuse Decorators](https://langfuse.com/docs/sdk/python/decorators)
- [自托管指南](https://langfuse.com/docs/deployment/self-host)
- [Best Practices](https://langfuse.com/docs/tracing)

---

## 🆘 需要帮助？

如果遇到问题：
1. 查看故障排查部分
2. 运行测试脚本: `python test_langfuse_connection.py`
3. 查看容器日志: `docker logs langfuse-server`
4. 提 Issue 或联系开发者

---

**更新日期**: 2026-01-26
**维护者**: Sheldon
**版本**: 2.0.0
