# Langfuse 集成最佳实践

## 🎯 核心原则：最小化代码入侵

好的可观测性集成应该：
- ✅ **对业务代码影响最小**
- ✅ **易于启用/禁用**
- ✅ **无需改变函数签名**
- ✅ **自动追踪，无需手动调用**

## ✅ 推荐方式：OpenAI Wrapper（我们使用的方案）

### 原理
Langfuse 提供了 OpenAI SDK 的包装器，可以**自动拦截所有 LLM 调用**，无需修改业务代码。

### 实现（3步）

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

### 优势对比

| 方式 | 代码修改 | 函数签名变化 | 易于禁用 | 自动追踪 Token |
|------|---------|-------------|---------|--------------|
| **OpenAI Wrapper** ✅ | 1行 | 无 | ✅ | ✅ |
| 手动 trace | 每个函数 10+ 行 | 需添加 trace_id | ❌ | ❌ |
| 装饰器 | 每个函数 1 行 | 无 | ✅ | ❌ |

## ❌ 不推荐：入侵式手动追踪

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

## 🔧 其他集成方式对比

### 方式 1: 装饰器（适用于特定函数追踪）

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

### 方式 2: LangChain 集成（如果使用 LangChain）

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

### 方式 3: Context Manager（适用于代码块追踪）

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

## 📊 我们的集成方案总结

### 当前实现（推荐）

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

### 未来扩展（可选）

如果需要追踪更多内容（如检索、文档处理），可以添加：

```python
# 方案 A: 装饰器（推荐）
@observe()
def retrieve(self, question: str):
    # ... 检索逻辑

# 方案 B: Context Manager
with langfuse.trace(name="extract_document"):
    # ... 提取逻辑
```

## 🎓 学习资源

- [Langfuse OpenAI Integration](https://langfuse.com/docs/integrations/openai)
- [Langfuse Decorators](https://langfuse.com/docs/sdk/python/decorators)
- [Best Practices](https://langfuse.com/docs/tracing)

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

## ✅ 总结

**最佳实践金字塔**（从简单到复杂）：

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
