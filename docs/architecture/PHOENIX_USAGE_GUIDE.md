# Phoenix 使用指南 - 两种方式对比

## 核心问题：必须封装吗？

**答案：完全不需要！** Phoenix Instrumentor 可以直接调用，封装只是为了方便管理。

## 方式对比

### 方式 1：自动注入（推荐，项目当前使用）

**优点**：
- ✅ 一次配置，自动检测所有已安装的 Instrumentor
- ✅ 零代码修改，启动时自动生效
- ✅ 统一管理，方便启用/禁用

**实现**：
```python
# backend/core/phoenix_observability.py (已实现)
class PhoenixTracer:
    def _auto_instrument(self):
        """自动注入所有已安装的 Instrumentor"""
        instrumentors = [
            ('openai', 'openinference.instrumentation.openai', 'OpenAIInstrumentor'),
            ('anthropic', 'openinference.instrumentation.anthropic', 'AnthropicInstrumentor'),
            # ... 更多
        ]

        for pkg, module_path, class_name in instrumentors:
            try:
                module = __import__(module_path, fromlist=[class_name])
                instrumentor = getattr(module, class_name)
                instrumentor().instrument(tracer_provider=self.tracer_provider)
            except ImportError:
                pass  # 未安装，跳过
```

**使用**：
```python
# backend/server.py
from backend.core.phoenix_observability import get_phoenix_tracer

# 启动时自动初始化（只需一行）
phoenix_tracer = get_phoenix_tracer()

# 之后所有 LLM 调用自动被追踪！
from openai import OpenAI
client = OpenAI(api_key="...")
client.chat.completions.create(...)  # ✅ 自动追踪
```

**添加新 LLM**：
```bash
# 1. 安装对应的包
pip install openinference-instrumentation-anthropic

# 2. 重启服务（无需修改代码）
./scripts/restart.sh

# 3. Anthropic 自动被追踪！
from anthropic import Anthropic
client = Anthropic(api_key="...")
client.messages.create(...)  # ✅ 自动追踪
```

---

### 方式 2：直接调用（最简单，不需要封装）

**优点**：
- ✅ 最直接，代码最少
- ✅ 不需要封装类
- ✅ 官方推荐方式

**完整示例**：
```python
# your_app.py
from phoenix.otel import register
from openinference.instrumentation.openai import OpenAIInstrumentor

# 1. 注册 Phoenix（只需一次）
tracer_provider = register(
    project_name="my-app",
    endpoint="http://localhost:4317"
)

# 2. 注入 OpenAI Instrumentor（只需一次）
OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)

# 3. 正常使用，自动追踪
from openai import OpenAI
client = OpenAI(api_key="...")
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
# ✅ 这个调用会被自动追踪！
```

**添加其他 LLM**：
```python
# 只需要多调用一次 instrument()
from openinference.instrumentation.anthropic import AnthropicInstrumentor

AnthropicInstrumentor().instrument(tracer_provider=tracer_provider)

# 然后就能追踪 Anthropic 了
from anthropic import Anthropic
client = Anthropic(api_key="...")
response = client.messages.create(...)  # ✅ 自动追踪
```

---

### 方式 3：最简单方式（如果不需要自定义）

**Phoenix 提供了更简单的 API**：

```python
# your_app.py
import phoenix as px

# 1. 启动 Phoenix（一行搞定）
px.launch_app()

# 2. 自动注入所有已安装的 Instrumentor
from openinference.instrumentation.openai import OpenAIInstrumentor
OpenAIInstrumentor().instrument()  # 不需要 tracer_provider

# 3. 正常使用
from openai import OpenAI
client = OpenAI(api_key="...")
client.chat.completions.create(...)  # ✅ 自动追踪
```

**访问 UI**：
```bash
# Phoenix 会自动在后台启动服务
# 访问: http://localhost:6006
```

---

## 三种方式对比

| 特性 | 方式 1: 自动注入封装 | 方式 2: 直接调用 | 方式 3: 最简方式 |
|------|---------------------|----------------|----------------|
| 代码量 | 中等（封装后简单） | 少（2-3 行） | 最少（1-2 行） |
| 灵活性 | 高（统一管理） | 高（完全控制） | 低（自动化） |
| 易用性 | 高（零配置） | 中（需要手动） | 最高（开箱即用） |
| 适用场景 | 生产环境 | 需要精细控制 | 快速原型/开发 |
| 当前项目 | ✅ 使用中 | 可选 | 可选 |

## 为什么项目使用方式 1？

```python
# 优势：统一管理，环境变量控制
PHOENIX_ENABLED=true   # 启用
PHOENIX_ENABLED=false  # 禁用

# 如果用方式 2，需要到处添加 if 判断
if os.getenv('PHOENIX_ENABLED') == 'true':
    OpenAIInstrumentor().instrument(...)
    AnthropicInstrumentor().instrument(...)
    # ... 每个文件都要重复
```

## 实际应用示例

### 场景 1: 只用 OpenAI（DeepSeek）

**方式 1（项目当前）**：
```python
# 无需修改，已自动启用
```

**方式 2（直接调用）**：
```python
from phoenix.otel import register
from openinference.instrumentation.openai import OpenAIInstrumentor

register(project_name="app", endpoint="http://localhost:4317")
OpenAIInstrumentor().instrument()
```

**方式 3（最简）**：
```python
import phoenix as px
px.launch_app()

from openinference.instrumentation.openai import OpenAIInstrumentor
OpenAIInstrumentor().instrument()
```

---

### 场景 2: 同时用 OpenAI + Anthropic

**方式 1（项目当前）**：
```bash
# 1. 安装包
pip install openinference-instrumentation-anthropic

# 2. 重启服务（自动检测）
./scripts/restart.sh

# ✅ 完成！两个都被追踪
```

**方式 2（直接调用）**：
```python
from phoenix.otel import register
from openinference.instrumentation.openai import OpenAIInstrumentor
from openinference.instrumentation.anthropic import AnthropicInstrumentor

tracer = register(project_name="app")
OpenAIInstrumentor().instrument(tracer_provider=tracer)
AnthropicInstrumentor().instrument(tracer_provider=tracer)
```

**方式 3（最简）**：
```python
import phoenix as px
px.launch_app()

from openinference.instrumentation.openai import OpenAIInstrumentor
from openinference.instrumentation.anthropic import AnthropicInstrumentor

OpenAIInstrumentor().instrument()
AnthropicInstrumentor().instrument()
```

---

### 场景 3: 使用 LiteLLM（100+ LLM）

**方式 1（项目当前）**：
```bash
pip install openinference-instrumentation-litellm
./scripts/restart.sh
# ✅ 自动支持所有 LiteLLM 的 100+ LLM
```

**方式 2（直接调用）**：
```python
from phoenix.otel import register
from openinference.instrumentation.litellm import LiteLLMInstrumentor

register(project_name="app")
LiteLLMInstrumentor().instrument()

# 现在可以用任何 LLM
from litellm import completion
completion(model="gpt-4", messages=[...])        # OpenAI
completion(model="claude-3", messages=[...])     # Anthropic
completion(model="deepseek-chat", messages=[...]) # DeepSeek
# 全部自动追踪 ✅
```

---

## instrument() 方法的本质

**问题：为什么调用一次就永久生效？**

```python
# 底层实现（简化）
class OpenAIInstrumentor:
    def instrument(self, tracer_provider=None):
        """Monkey Patch OpenAI 类"""
        import openai

        # 保存原始方法
        original_create = openai.ChatCompletion.create

        # 定义包装方法
        def wrapped_create(*args, **kwargs):
            # 1. 创建 span（追踪记录）
            with tracer.start_span("openai.chat.create") as span:
                # 2. 记录请求参数
                span.set_attribute("model", kwargs.get("model"))
                span.set_attribute("messages", kwargs.get("messages"))

                # 3. 调用原始方法
                response = original_create(*args, **kwargs)

                # 4. 记录响应
                span.set_attribute("response", response)

                return response

        # 替换原始方法（全局生效！）
        openai.ChatCompletion.create = wrapped_create
```

**关键点**：
1. `instrument()` 修改的是 **模块级别的类/方法**
2. 修改后，所有使用该模块的代码都会被影响
3. 只需要调用一次，全局永久生效
4. 不需要每次调用都封装

---

## 核心结论

### ✅ 推荐做法

**对于项目开发（当前方式）**：
```python
# 使用统一的 PhoenixTracer，自动管理
from backend.core.phoenix_observability import get_phoenix_tracer
phoenix_tracer = get_phoenix_tracer()
# 之后无需任何操作，自动追踪所有 LLM
```

**对于快速原型/脚本**：
```python
# 直接调用，最简单
from phoenix.otel import register
from openinference.instrumentation.openai import OpenAIInstrumentor

register(project_name="prototype")
OpenAIInstrumentor().instrument()
# 完成！
```

### ❌ 不需要的做法

```python
# ❌ 不需要每次都封装
class MyInstrumentor:
    def instrument_openai(self):
        OpenAIInstrumentor().instrument()

    def instrument_anthropic(self):
        AnthropicInstrumentor().instrument()

# ❌ 不需要每个文件都调用
# every_file.py
OpenAIInstrumentor().instrument()  # 只需要在启动时调用一次！
```

---

## 总结

| 问题 | 答案 |
|------|------|
| 必须封装吗？ | ❌ 不需要 |
| 可以直接调用吗？ | ✅ 完全可以 |
| 调用一次就够吗？ | ✅ 是的，全局生效 |
| 哪种方式最好？ | 看场景：项目用封装，脚本用直接 |

**最简使用示例**：
```python
# 仅需 3 行！
from phoenix.otel import register
from openinference.instrumentation.openai import OpenAIInstrumentor

register(); OpenAIInstrumentor().instrument()

# 之后所有 OpenAI 调用自动追踪 ✅
```

---

**创建日期**: 2026-01-31
**维护者**: Sheldon
**版本**: 1.0.0
