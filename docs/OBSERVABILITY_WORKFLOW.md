# Phoenix + Langfuse 配合使用工作流

## 核心理念

- **Phoenix**：开发阶段的实验室 🧪
- **Langfuse**：生产阶段的监控台 📊
- **互不冲突**：可以同时启用，数据独立

## 完整工作流

### 阶段 1：开发和优化（使用 Phoenix）

```bash
# 配置
PHOENIX_ENABLED=true
LANGFUSE_ENABLED=false  # 开发阶段可以不启用
```

**步骤 1：Prompt 开发**
1. 写一个初版 Prompt
2. 在代码中调用 LLM
3. Phoenix 自动追踪所有调用
4. 在 http://localhost:6006 查看结果

**步骤 2：Prompt 优化**
1. 在 Phoenix UI 选择一个追踪记录
2. 点击 "Open in Playground"
3. 修改 Prompt，实时对比输出
4. 测试不同的模型（GPT-3.5 vs GPT-4）
5. 调整参数（temperature, max_tokens）
6. 找到最佳组合

**步骤 3：评估验证**
```python
from phoenix.evals import (
    llm_classify,
    OpenAIModel,
    run_evals
)

# 准备测试数据集
test_cases = [
    {"input": "问题1", "expected": "答案1"},
    {"input": "问题2", "expected": "答案2"},
    # ... 50个测试用例
]

# 评估 Prompt 质量
eval_model = OpenAIModel(model="gpt-4", temperature=0)

# 评估准确性
accuracy = llm_classify(
    dataframe=test_cases,
    model=eval_model,
    template="Is this answer correct? Answer YES or NO.",
    rails=["YES", "NO"]
)

# 评估相关性
relevance = llm_classify(
    dataframe=test_cases,
    model=eval_model,
    template="Is this answer relevant? Answer YES or NO.",
    rails=["YES", "NO"]
)

print(f"准确率: {accuracy.score()}")
print(f"相关性: {relevance.score()}")
```

**步骤 4：A/B 测试**
```python
from phoenix.experiments import run_experiment

# 对比两个版本
experiment_results = run_experiment(
    dataset=test_cases,
    task=your_qa_function,
    experiment_name="prompt-v2-vs-v3",
    evaluators=[accuracy_evaluator, relevance_evaluator]
)

# 查看对比结果
print(experiment_results.summary())
# Prompt v2: 准确率 85%, 相关性 90%
# Prompt v3: 准确率 92%, 相关性 88%
# → 选择 v3（准确性更重要）
```

---

### 阶段 2：测试环境（同时启用）

```bash
# 配置
PHOENIX_ENABLED=true   # 继续优化
LANGFUSE_ENABLED=true  # 开始收集生产数据
```

**目标：**
- Phoenix：继续监控性能，发现问题
- Langfuse：收集真实数据，准备上线

**操作：**
```python
# 两个追踪器同时初始化
from backend.core.phoenix_observability import get_phoenix_tracer
from backend.core.observability import get_tracer as get_langfuse_tracer

phoenix_tracer = get_phoenix_tracer()    # 自动追踪
langfuse_tracer = get_langfuse_tracer()  # 手动包装

# OpenAI 客户端
client = OpenAI(api_key=api_key)

# Langfuse wrapper
if langfuse_tracer.enabled:
    client = langfuse_tracer.wrap_openai(client)

# 使用客户端（两个系统都会记录）
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": query}]
)

# Phoenix：查看技术指标（延迟、Token）
# Langfuse：查看业务指标（成本、用户行为）
```

---

### 阶段 3：生产环境（使用 Langfuse）

```bash
# 配置
PHOENIX_ENABLED=false   # 关闭或采样
LANGFUSE_ENABLED=true   # 主要监控工具
```

**为什么切换？**
- 生产环境重点是监控和分析，不需要实验功能
- Langfuse 的分析功能更强大
- 降低系统开销

**可选：保留 Phoenix 采样追踪**
```bash
PHOENIX_ENABLED=true
PHOENIX_SAMPLING_RATE=0.1  # 只追踪 10% 的请求
LANGFUSE_ENABLED=true
```

**Langfuse 监控内容：**
1. **成本追踪**
   - 每日成本趋势
   - 按用户/功能分组的成本
   - 预警：成本超过预算

2. **性能监控**
   - 平均响应时间
   - 慢查询分析
   - 错误率追踪

3. **用户分析**
   - 哪些用户使用最频繁？
   - 哪些问题被问得最多？
   - 用户满意度如何？

4. **质量监控**
   - Token 使用是否合理？
   - 是否有异常调用？
   - 输出质量是否稳定？

---

### 阶段 4：持续优化（回到 Phoenix）

**触发条件：**
- Langfuse 发现问题（例如：成本过高、响应慢）
- 收到用户反馈（例如：答案质量下降）
- 需要添加新功能

**流程：**
```bash
# 1. 从 Langfuse 导出问题数据
curl -X GET "https://cloud.langfuse.com/api/traces?filter=slow" \
  -H "Authorization: Bearer $LANGFUSE_API_KEY" \
  > slow_traces.json

# 2. 在开发环境重现问题
PHOENIX_ENABLED=true
LANGFUSE_ENABLED=false

# 3. 使用 Phoenix 诊断
# - Playground 中重放慢查询
# - 分析为什么慢（Token 太多？模型选择？）
# - 优化 Prompt

# 4. 评估改进效果
python evaluate_optimization.py

# 5. 部署到生产
# 6. 在 Langfuse 验证改进（成本降低了吗？速度提升了吗？）
```

---

## 具体使用场景

### 场景 1：开发新功能

**需求**：添加"文档摘要"功能

**使用 Phoenix**：
```python
# 1. 开发初版
def summarize_document(doc_text):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "user",
            "content": f"请总结这段文字：\n{doc_text}"
        }]
    )
    return response.choices[0].message.content

# 2. 在 Phoenix Playground 测试
# - 调整 Prompt
# - 对比 gpt-3.5-turbo vs gpt-4
# - 测试不同长度的文档

# 3. 评估质量
test_docs = load_test_documents()
results = evaluate_summaries(test_docs)
# 准确率: 75%（不够好）

# 4. 优化 Prompt
def summarize_document_v2(doc_text):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{
            "role": "system",
            "content": "你是文档摘要专家，擅长提炼核心观点。"
        }, {
            "role": "user",
            "content": f"请用3-5句话总结这段文字的核心观点：\n{doc_text}"
        }]
    )
    return response.choices[0].message.content

# 5. 再次评估
results = evaluate_summaries(test_docs)
# 准确率: 92%（达标！）
```

**上线后，使用 Langfuse**：
- 监控实际使用情况
- 成本：每次摘要 $0.05
- 性能：平均 3 秒
- 用户反馈：90% 满意

---

### 场景 2：优化成本

**问题**：Langfuse 显示成本过高

**Langfuse 分析**：
```
月度报告：
- 总成本: $500
- 主要花费: QA 功能（$400, 80%）
- 平均每次调用: $0.10
- 原因: 使用 GPT-4 + 长上下文
```

**使用 Phoenix 优化**：
```python
# 1. 在 Phoenix 中重现场景
# 2. 测试方案 A: 缩短上下文
def qa_optimized_v1(query, context):
    # 只保留最相关的 top-3 段落
    context = filter_top_k(context, k=3)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[...]
    )
    return response

# 3. 测试方案 B: 使用 GPT-3.5
def qa_optimized_v2(query, context):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # 便宜 10 倍
        messages=[...]
    )
    return response

# 4. A/B 测试
experiment = run_experiment(
    dataset=test_cases,
    tasks=[qa_optimized_v1, qa_optimized_v2],
    evaluators=[accuracy, relevance, cost]
)

# 结果：
# 方案 A (GPT-4 + 短上下文): 准确率 88%, 成本 $0.05
# 方案 B (GPT-3.5 + 长上下文): 准确率 82%, 成本 $0.01
# → 选择方案 A（平衡质量和成本）
```

**部署后，Langfuse 验证**：
```
下月报告：
- 总成本: $250（降低 50%！）
- QA 功能: $200
- 平均每次调用: $0.05
- 质量: 准确率维持在 88%
```

---

### 场景 3：诊断问题

**问题**：用户反馈答案质量下降

**Langfuse 分析**：
- 错误率从 0.5% 上升到 5%
- 问题集中在某类问题上
- 导出问题数据

**使用 Phoenix 诊断**：
```python
# 1. 加载问题数据
problem_cases = load_from_langfuse("error_traces.json")

# 2. 在 Phoenix 中重放
for case in problem_cases:
    response = qa_function(case["query"])
    # Phoenix 自动记录

# 3. 在 Playground 分析
# - 发现：某些问题的上下文检索失败
# - 原因：向量数据库更新后索引损坏

# 4. 修复并验证
fix_vector_index()
test_results = evaluate_fixed_system(problem_cases)
# 错误率降到 0.8%

# 5. 部署修复
```

---

## 配置示例

### 开发环境（`dev.env`）

```bash
# Phoenix - 实验和优化
PHOENIX_ENABLED=true
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:4317
PHOENIX_PROJECT_NAME=knowledge-weaver-dev

# Langfuse - 可选
LANGFUSE_ENABLED=false
```

### 测试环境（`test.env`）

```bash
# Phoenix - 继续监控
PHOENIX_ENABLED=true
PHOENIX_COLLECTOR_ENDPOINT=http://test-phoenix:4317
PHOENIX_PROJECT_NAME=knowledge-weaver-test

# Langfuse - 开始收集数据
LANGFUSE_ENABLED=true
LANGFUSE_HOST=http://test-langfuse:3000
```

### 生产环境（`prod.env`）

```bash
# Phoenix - 采样追踪（可选）
PHOENIX_ENABLED=true
PHOENIX_SAMPLING_RATE=0.05  # 5% 采样
PHOENIX_COLLECTOR_ENDPOINT=http://prod-phoenix:4317
PHOENIX_PROJECT_NAME=knowledge-weaver-prod

# Langfuse - 主要监控
LANGFUSE_ENABLED=true
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_PUBLIC_KEY=pk_prod_xxx
LANGFUSE_SECRET_KEY=sk_prod_xxx
```

---

## 性能开销

### 单独使用

- **Phoenix alone**: < 1-2% 延迟增加
- **Langfuse alone**: < 2-3% 延迟增加

### 同时使用

- **Both enabled**: < 3-5% 延迟增加
- **采样后**: < 1-2% 延迟增加

**结论**：开销可以接受，尤其是采样后。

---

## 最佳实践总结

### ✅ 推荐做法

1. **开发阶段**：只用 Phoenix
   - 快速实验
   - 无需云服务
   - 完全免费

2. **测试阶段**：两个都启用
   - Phoenix：技术指标
   - Langfuse：业务指标

3. **生产阶段**：主要用 Langfuse
   - Phoenix 可选（采样）
   - Langfuse 用于监控

4. **发现问题**：回到 Phoenix
   - 诊断和优化
   - 评估改进效果

### ❌ 不推荐做法

1. ~~生产环境启用 Phoenix 全量追踪~~
   - 开销较大
   - 不需要实验功能

2. ~~开发阶段用 Langfuse~~
   - 实验功能弱
   - 需要云服务

3. ~~同时使用但不采样~~
   - 性能开销叠加
   - 数据冗余

---

## 数据流向

```
用户请求
  ↓
应用代码
  ↓
OpenAI Client
  ├─→ Phoenix (OpenTelemetry)
  │     ├─ 技术指标（延迟、Token）
  │     ├─ Prompt/Response
  │     └─ 实验数据
  │
  └─→ Langfuse (Wrapper)
        ├─ 业务指标（成本、用户）
        ├─ Prompt/Response
        └─ 分析数据
```

**重要**：两个系统的数据是独立的，互不影响。

---

## 工具选择决策树

```
需要做什么？
│
├─ 开发新功能 / 优化 Prompt
│  └─→ 使用 Phoenix ✅
│
├─ 生产环境监控
│  └─→ 使用 Langfuse ✅
│
├─ 评估和 A/B 测试
│  └─→ 使用 Phoenix ✅
│
├─ 成本分析和追踪
│  └─→ 使用 Langfuse ✅
│
├─ 诊断生产问题
│  ├─ 先看 Langfuse（发现问题）
│  └─ 再用 Phoenix（诊断和修复）
│
└─ 全流程覆盖
   └─→ 两个都用 ✅
```

---

**更新日期**: 2026-01-26
**维护者**: Sheldon
