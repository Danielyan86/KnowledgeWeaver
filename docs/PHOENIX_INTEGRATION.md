# Phoenix 集成指南

## 概述

Phoenix 是 Arize-AI 开源的 AI 可观测性和评估平台，基于 OpenTelemetry 标准。本文档介绍如何将 Phoenix 集成到 KnowledgeWeaver 项目中。

## Phoenix vs Langfuse

### 核心区别

| 特性 | Phoenix | Langfuse |
|------|---------|----------|
| **主要用途** | 实验、评估、Prompt 优化 | 生产环境监控和分析 |
| **技术基础** | OpenTelemetry（开放标准） | 自有协议 |
| **部署** | 完全开源，本地部署 | 云端或自托管 |
| **零代码追踪** | ✅ | ❌（需要装饰器/wrapper） |
| **数据集管理** | ✅ | ❌ |
| **实验追踪** | ✅ | ❌ |
| **Prompt Playground** | ✅ 强大 | ⚠️ 基础 |
| **LLM 评估** | ✅ 内置多种评估器 | ⚠️ 需自建 |
| **分析仪表板** | ⚠️ 基础 | ✅ 强大 |
| **成熟度** | 较新（2023+） | 更成熟 |

### 适用场景

**Phoenix 适合：**
- 开发阶段的快速迭代
- Prompt 工程和优化
- A/B 测试和实验
- 模型评估和对比
- 本地开发（无需云服务）

**Langfuse 适合：**
- 生产环境长期监控
- 详细的使用分析
- 成本追踪
- 团队协作

## 推荐方案

### 方案 1：双追踪（推荐）

同时使用 Phoenix 和 Langfuse，各取所长：

```python
# Phoenix：开发环境，用于实验和评估
if os.getenv('ENVIRONMENT') == 'development':
    from phoenix.otel import register
    tracer_provider = register(
        project_name="knowledge-weaver-dev",
        endpoint="http://localhost:6006/v1/traces"
    )

# Langfuse：生产环境，用于监控
if os.getenv('ENVIRONMENT') == 'production':
    from langfuse import Langfuse
    langfuse = Langfuse()
```

### 方案 2：Phoenix 优先

如果更关注实验和评估，可以优先使用 Phoenix：

- Phoenix 基于 OpenTelemetry，数据可以导出到任何兼容系统
- 未来可以轻松切换到其他工具
- 本地部署，无需担心数据隐私

### 方案 3：按功能分工

- **追踪**：Phoenix（自动追踪，零代码修改）
- **评估**：Phoenix（内置评估器）
- **分析**：Langfuse（导出 Phoenix 数据到 Langfuse）

## 安装 Phoenix

### 1. 安装 Python 包

```bash
pip install arize-phoenix
pip install arize-phoenix-otel
pip install openinference-instrumentation-openai
```

### 2. 启动 Phoenix 服务器

**方式 1：Docker（推荐）**

```bash
docker run -d \
  --name phoenix \
  -p 6006:6006 \
  -p 4317:4317 \
  -e PHOENIX_WORKING_DIR=/data \
  -v $(pwd)/data/phoenix:/data \
  arizephoenix/phoenix:latest
```

**方式 2：Python**

```bash
python -m phoenix.server.main serve
```

访问 http://localhost:6006 查看 Phoenix UI。

### 3. 配置环境变量

编辑 `.env` 文件：

```bash
# Phoenix 配置
PHOENIX_ENABLED=true
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:4317
PHOENIX_PROJECT_NAME=knowledge-weaver
```

## 集成代码

### 1. 创建 Phoenix 追踪器

创建 `backend/core/phoenix_observability.py`：

```python
"""
Phoenix Observability
基于 OpenTelemetry 的可观测性
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class PhoenixTracer:
    """Phoenix 追踪器（单例）"""

    _instance: Optional['PhoenixTracer'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self.enabled = os.getenv('PHOENIX_ENABLED', 'false').lower() == 'true'
        self.tracer_provider = None

        if self.enabled:
            try:
                from phoenix.otel import register

                endpoint = os.getenv(
                    'PHOENIX_COLLECTOR_ENDPOINT',
                    'http://localhost:4317'
                )
                project_name = os.getenv(
                    'PHOENIX_PROJECT_NAME',
                    'knowledge-weaver'
                )

                # 注册 OpenTelemetry
                self.tracer_provider = register(
                    project_name=project_name,
                    endpoint=endpoint
                )

                # 自动追踪 OpenAI
                from openinference.instrumentation.openai import OpenAIInstrumentor
                OpenAIInstrumentor().instrument(tracer_provider=self.tracer_provider)

                print(f"✅ Phoenix 已启用: {endpoint}")
            except ImportError as e:
                print(f"⚠️ Phoenix 包未安装: {e}")
                self.enabled = False
            except Exception as e:
                print(f"⚠️ Phoenix 初始化失败: {e}")
                self.enabled = False
        else:
            print("ℹ️ Phoenix 追踪已禁用")

        self._initialized = True

    def instrument_langchain(self):
        """追踪 LangChain（如果使用）"""
        if not self.enabled:
            return

        try:
            from openinference.instrumentation.langchain import LangChainInstrumentor
            LangChainInstrumentor().instrument(tracer_provider=self.tracer_provider)
            print("✅ LangChain 追踪已启用")
        except ImportError:
            pass

    def instrument_llama_index(self):
        """追踪 LlamaIndex（如果使用）"""
        if not self.enabled:
            return

        try:
            from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
            LlamaIndexInstrumentor().instrument(tracer_provider=self.tracer_provider)
            print("✅ LlamaIndex 追踪已启用")
        except ImportError:
            pass


# 全局单例
_phoenix_tracer: Optional[PhoenixTracer] = None


def get_phoenix_tracer() -> PhoenixTracer:
    """获取 Phoenix 追踪器单例"""
    global _phoenix_tracer
    if _phoenix_tracer is None:
        _phoenix_tracer = PhoenixTracer()
    return _phoenix_tracer
```

### 2. 修改 LLM 客户端初始化

在 `backend/core/embeddings/service.py` 或其他使用 OpenAI 的地方：

```python
from backend.core.phoenix_observability import get_phoenix_tracer

# 初始化 Phoenix（在创建 OpenAI 客户端之前）
phoenix_tracer = get_phoenix_tracer()

# 创建 OpenAI 客户端（Phoenix 会自动追踪）
client = OpenAI(api_key=api_key, base_url=base_url)
```

### 3. 双追踪集成（可选）

如果同时使用 Phoenix 和 Langfuse：

```python
from backend.core.observability import get_tracer as get_langfuse_tracer
from backend.core.phoenix_observability import get_phoenix_tracer

# 初始化两个追踪器
langfuse_tracer = get_langfuse_tracer()
phoenix_tracer = get_phoenix_tracer()

# OpenAI 客户端
client = OpenAI(api_key=api_key, base_url=base_url)

# Langfuse wrapper（需要显式包装）
if langfuse_tracer.enabled:
    client = langfuse_tracer.wrap_openai(client)

# Phoenix 自动追踪（无需额外代码）
# OpenAI 调用会同时发送到两个系统
```

## 使用 Phoenix 功能

### 1. 查看追踪数据

访问 http://localhost:6006，查看：
- 所有 LLM 调用的详细追踪
- Token 使用统计
- 延迟分析
- 错误追踪

### 2. Prompt Playground

在 Phoenix UI 中：
1. 选择一个追踪记录
2. 点击 "Open in Playground"
3. 修改 Prompt，对比不同版本的输出
4. 测试不同的模型和参数

### 3. 评估（Evaluation）

```python
from phoenix.evals import (
    llm_classify,
    OpenAIModel,
    run_evals
)

# 定义评估模型
eval_model = OpenAIModel(
    model="gpt-4",
    temperature=0
)

# 评估 Prompt 质量
results = llm_classify(
    dataframe=your_data,
    model=eval_model,
    template="Is this response helpful? Answer YES or NO.",
    rails=["YES", "NO"]
)
```

### 4. 数据集管理

```python
from phoenix.datasets import Dataset

# 创建数据集
dataset = Dataset(
    name="qa-test-set",
    examples=[
        {"input": "问题1", "expected_output": "答案1"},
        {"input": "问题2", "expected_output": "答案2"},
    ]
)

# 保存数据集
dataset.save()

# 加载数据集
dataset = Dataset.load("qa-test-set")
```

### 5. 实验追踪

```python
from phoenix.experiments import run_experiment

# 运行实验
results = run_experiment(
    dataset=dataset,
    task=your_qa_function,
    experiment_name="prompt-v2-test",
    evaluators=[
        accuracy_evaluator,
        relevance_evaluator
    ]
)

# 查看结果
print(results.summary())
```

## Docker Compose 配置

创建 `docker-compose.phoenix.yml`：

```yaml
version: '3.8'

services:
  phoenix:
    image: arizephoenix/phoenix:latest
    container_name: phoenix
    ports:
      - "6006:6006"  # Phoenix UI
      - "4317:4317"  # OpenTelemetry gRPC
      - "4318:4318"  # OpenTelemetry HTTP
    environment:
      - PHOENIX_WORKING_DIR=/data
    volumes:
      - ./data/phoenix:/data
    restart: unless-stopped
```

启动：

```bash
docker-compose -f docker-compose.phoenix.yml up -d
```

## 性能影响

### Phoenix 性能开销

- **追踪开销**：< 1-2% 延迟增加
- **内存开销**：< 50MB（追踪器）
- **网络**：异步发送，不阻塞主流程

### 优化建议

1. **采样**：生产环境可以采样追踪

```python
from phoenix.otel import register

register(
    project_name="knowledge-weaver",
    endpoint="http://localhost:4317",
    # 只追踪 10% 的请求
    sampler=TraceIdRatioBased(0.1)
)
```

2. **批量发送**：配置批处理

```python
register(
    project_name="knowledge-weaver",
    endpoint="http://localhost:4317",
    # 每 1000 条或 5 秒发送一次
    batch_export_config={
        "max_queue_size": 1000,
        "schedule_delay_millis": 5000
    }
)
```

## 迁移指南

### 从 Langfuse 迁移到 Phoenix

**优点：**
- 零代码修改（OpenTelemetry 自动追踪）
- 更强大的实验和评估功能
- 完全开源，本地部署

**缺点：**
- 分析功能不如 Langfuse 成熟
- 需要自己管理基础设施

**步骤：**

1. 安装 Phoenix
2. 启用 Phoenix 追踪
3. 逐步移除 Langfuse 装饰器和 wrapper
4. 对比数据，确认追踪正常
5. 停用 Langfuse（保留历史数据）

### 共存方案

如果想同时使用：

```python
# Phoenix：自动追踪所有 OpenAI 调用
phoenix_tracer = get_phoenix_tracer()

# Langfuse：额外追踪特定函数
@langfuse_tracer.observe()
def important_function():
    # OpenAI 调用会被两个系统追踪
    pass
```

## 常见问题

### Q: Phoenix 和 Langfuse 可以同时使用吗？

A: 可以。Phoenix 基于 OpenTelemetry，Langfuse 使用独立的 wrapper，两者不冲突。

### Q: 追踪数据存储在哪里？

A: Phoenix 默认存储在 SQLite（本地）或 PostgreSQL（生产）。可以导出到 S3 或其他存储。

### Q: 如何导出数据？

A: Phoenix 支持导出为 Parquet、JSON 等格式，也可以通过 API 查询。

### Q: 生产环境推荐配置？

A:
- 使用 PostgreSQL 存储
- 启用采样（10-50%）
- 配置数据保留策略
- 使用 Docker/K8s 部署

### Q: 如何关闭追踪？

A: 设置环境变量 `PHOENIX_ENABLED=false`

## 最佳实践

1. **开发阶段**：使用 Phoenix 进行快速迭代和实验
2. **生产环境**：根据需求选择 Phoenix 或 Langfuse
3. **混合使用**：Phoenix（实验）+ Langfuse（监控）
4. **定期评估**：使用 Phoenix 的评估功能定期测试 Prompt 质量
5. **数据集管理**：使用 Phoenix 管理测试数据集，便于回归测试

## 相关资源

- [Phoenix 官方文档](https://docs.arize.com/phoenix)
- [Phoenix GitHub](https://github.com/Arize-ai/phoenix)
- [OpenInference](https://github.com/Arize-ai/openinference)
- [OpenTelemetry](https://opentelemetry.io/)

---

**更新日期**: 2026-01-26
**维护者**: Sheldon
