# Langfuse 集成指南

## 📖 概述

Langfuse 是一个专为 LLM 应用设计的可观测性平台，可以帮助你监控和优化 KnowledgeWeaver 的问答系统。

**集成状态**: ✅ POC 已完成 - 使用 OpenAI Wrapper 非入侵式集成

**代码改动量**: 仅 **1 行代码** 🎉

**集成方式**: OpenAI Wrapper - 自动追踪所有 LLM 调用，无需修改业务代码

## 🎯 追踪内容

当前集成追踪以下操作：

### 1. 问答请求 (Trace)
- 用户问题
- 生成的答案
- 检索模式（auto/kg_only/rag_only/hybrid）
- 执行时间

### 2. 检索操作 (Span)
- 检索到的实体数量
- 检索到的关系数量
- 检索到的文档片段数量
- 检索策略和参数

### 3. LLM 调用 (Generation)
- 模型名称
- 输入 prompt
- 生成的答案
- Token 使用量（prompt tokens, completion tokens）
- 成本统计

## 🚀 快速开始

### 方案 A: 使用 Langfuse Cloud（最快）

1. **注册 Langfuse Cloud 账号**
   - 访问: https://cloud.langfuse.com
   - 注册免费账号
   - 创建新项目

2. **获取 API Keys**
   - 在项目设置中找到 Public Key 和 Secret Key

3. **配置环境变量**
   编辑 `.env` 文件，添加以下配置：
   ```bash
   # 启用 Langfuse
   LANGFUSE_ENABLED=true

   # Langfuse Cloud
   LANGFUSE_PUBLIC_KEY=pk-lf-xxx
   LANGFUSE_SECRET_KEY=sk-lf-xxx
   LANGFUSE_HOST=https://cloud.langfuse.com
   ```

4. **安装依赖并启动**
   ```bash
   pip install langfuse>=2.0.0
   python -m backend.server
   ```

5. **测试追踪**
   发送问答请求：
   ```bash
   curl -X POST http://localhost:9621/qa \
     -H "Content-Type: application/json" \
     -d '{
       "question": "什么是知识图谱？",
       "mode": "auto"
     }'
   ```

6. **查看追踪数据**
   - 访问 https://cloud.langfuse.com
   - 在 Traces 页面查看刚才的请求

### 方案 B: 自托管 Langfuse（推荐）

#### 优点
- ✅ 数据完全掌控
- ✅ 无需担心隐私
- ✅ 免费使用所有功能
- ✅ 可定制化

#### 部署步骤

1. **使用 Docker Compose 部署**

   创建 `docker-compose.langfuse.yml`:
   ```yaml
   version: '3.8'

   services:
     langfuse-server:
       image: langfuse/langfuse:latest
       ports:
         - "3000:3000"
       environment:
         - DATABASE_URL=postgresql://postgres:postgres@langfuse-db:5432/langfuse
         - NEXTAUTH_URL=http://localhost:3000
         - NEXTAUTH_SECRET=mysecret
         - SALT=mysalt
       depends_on:
         - langfuse-db

     langfuse-db:
       image: postgres:15
       environment:
         - POSTGRES_USER=postgres
         - POSTGRES_PASSWORD=postgres
         - POSTGRES_DB=langfuse
       volumes:
         - langfuse-db-data:/var/lib/postgresql/data

   volumes:
     langfuse-db-data:
   ```

2. **启动 Langfuse**
   ```bash
   docker-compose -f docker-compose.langfuse.yml up -d
   ```

3. **访问 Langfuse 界面**
   - 打开浏览器访问: http://localhost:3000
   - 创建管理员账号
   - 创建新项目并获取 API Keys

4. **配置 KnowledgeWeaver**
   编辑 `.env`:
   ```bash
   LANGFUSE_ENABLED=true
   LANGFUSE_PUBLIC_KEY=your_public_key
   LANGFUSE_SECRET_KEY=your_secret_key
   LANGFUSE_HOST=http://localhost:3000
   ```

5. **测试**
   ```bash
   # 安装依赖
   pip install langfuse>=2.0.0

   # 启动服务
   python -m backend.server

   # 发送测试请求
   curl -X POST http://localhost:9621/qa \
     -H "Content-Type: application/json" \
     -d '{"question": "测试问题", "mode": "auto"}'
   ```

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

### 3. Prompts 视图（未来扩展）
管理和版本化提示词模板

### 4. Datasets 视图（未来扩展）
创建测试集和基准测试

## 🔍 调试示例

### 查看特定问题的追踪

1. 在 Langfuse Dashboard 打开 Traces
2. 搜索问题关键词
3. 点击查看详细信息：
   - 检索了哪些实体和关系
   - 检索了哪些文档片段
   - LLM 输入的完整 prompt
   - 生成的答案
   - Token 使用量

### 分析性能瓶颈

1. 在 Traces 页面按执行时间排序
2. 找出慢查询
3. 查看是检索慢还是 LLM 生成慢
4. 针对性优化

### 成本分析

1. 在 Dashboard 首页查看总体统计
2. 按日期、模型查看成本趋势
3. 识别高成本操作
4. 优化 token 使用

## 🎯 下一步扩展

当前只集成了 `/qa` 端点，你可以继续扩展：

### 1. 追踪文档提取
在 `extractor.py` 和 `async_extractor.py` 中添加追踪：
```python
# 追踪每次实体提取
tracer.trace_llm_call(...)
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

## 🐛 故障排查

### 问题: Langfuse 初始化失败

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

### 问题: 看不到追踪数据

**检查**:
1. 确认 `LANGFUSE_ENABLED=true`
2. 查看服务启动日志，应该看到 "✅ Langfuse 已启用"
3. 检查是否有错误日志

**调试**:
```bash
# 查看详细日志
LANGFUSE_DEBUG=true python -m backend.server
```

### 问题: 追踪数据不完整

**原因**: 追踪数据是异步发送的，可能有延迟

**解决**: 等待几秒后刷新 Dashboard

## 📈 最佳实践

1. **开发环境**: 使用 Cloud 版本快速验证
2. **生产环境**: 使用自托管版本保证数据隐私
3. **定期分析**: 每周查看追踪数据，优化系统
4. **成本控制**: 监控 token 使用，避免意外高额账单
5. **用户反馈**: 收集真实用户反馈，持续改进

## 📚 更多资源

- [Langfuse 官方文档](https://langfuse.com/docs)
- [Python SDK 文档](https://langfuse.com/docs/sdk/python)
- [自托管指南](https://langfuse.com/docs/deployment/self-host)

## 🤝 反馈

如果在集成过程中遇到问题，请提 Issue 或联系开发者。
