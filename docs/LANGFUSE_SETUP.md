# Langfuse 自托管完整设置指南

## ✅ 已完成的部分

- ✅ Docker Compose 配置已创建
- ✅ Langfuse 服务已启动（v2版本，简化配置）
- ✅ PostgreSQL 数据库运行正常
- ✅ 集成代码已添加（OpenAI Wrapper 方式，仅1行代码）
- ✅ 测试脚本已创建

## 🚀 完成剩余配置（5 分钟）

### 步骤 1: 访问 Langfuse UI（1分钟）

打开浏览器访问:
```
http://localhost:3000
```

### 步骤 2: 创建账号和项目（2分钟）

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

### 步骤 3: 配置 KnowledgeWeaver（1分钟）

编辑 `.env` 文件，找到这部分（已预先添加）：

```bash
# Langfuse Configuration (自托管)
LANGFUSE_ENABLED=true
LANGFUSE_HOST=http://localhost:3000
LANGFUSE_PUBLIC_KEY=pk-lf-你的公钥  # ← 替换这里
LANGFUSE_SECRET_KEY=sk-lf-你的密钥   # ← 替换这里
```

**将 API Keys 替换为从 Langfuse UI 复制的值。**

### 步骤 4: 测试连接（1分钟）

```bash
# 1. 确保已安装 langfuse
pip install langfuse>=2.0.0

# 2. 运行测试脚本
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

### 步骤 5: 启动 KnowledgeWeaver（30秒）

```bash
python -m backend.server
```

**期望日志**：
```
✅ Langfuse 已启用: http://localhost:3000
✅ OpenAI 客户端已包装 Langfuse 追踪
启动服务: http://0.0.0.0:9621
```

### 步骤 6: 发送测试请求（30秒）

```bash
curl -X POST http://localhost:9621/qa \
  -H "Content-Type: application/json" \
  -d '{
    "question": "什么是知识图谱？",
    "mode": "auto"
  }'
```

### 步骤 7: 查看追踪数据（30秒）

1. 访问: http://localhost:3000/traces
2. 应该能看到刚才的问答请求
3. 点击查看详情，包含:
   - 用户问题
   - LLM 生成的答案
   - Token 使用量
   - 执行时间
   - 成本（如果配置了定价）

## 🎉 完成！

现在每次调用 `/qa` API 都会自动追踪到 Langfuse！

## 📊 Langfuse Dashboard 功能

### Traces（追踪）
- 查看所有问答请求
- 按时间、状态、延迟筛选
- 查看完整的输入/输出

### Generations（生成）
- 查看所有 LLM 调用
- Token 使用统计
- 成本分析
- 模型性能对比

### Dashboard（仪表盘）
- 总请求数
- Token 使用趋势
- 成本趋势
- 平均延迟

## 🔧 管理 Langfuse 服务

### 查看服务状态
```bash
docker ps | grep langfuse
```

### 查看日志
```bash
# Langfuse 服务日志
docker logs -f langfuse-server

# 数据库日志
docker logs -f langfuse-db
```

### 停止服务
```bash
docker compose -f docker-compose.langfuse.yml down
```

### 启动服务
```bash
docker compose -f docker-compose.langfuse.yml up -d
```

### 完全清理（包括数据）
```bash
docker compose -f docker-compose.langfuse.yml down -v
```

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

### 问题 2: Docker 容器启动失败

**检查**:
```bash
docker logs langfuse-server
docker logs langfuse-db
```

**解决**:
```bash
# 重启服务
docker compose -f docker-compose.langfuse.yml restart

# 完全重建
docker compose -f docker-compose.langfuse.yml down -v
docker compose -f docker-compose.langfuse.yml up -d
```

### 问题 3: 连接超时

**检查**:
```bash
# 测试端口是否开放
curl http://localhost:3000

# 确认容器运行
docker ps | grep langfuse
```

## 📈 下一步优化

### 1. 启用 HTTPS（生产环境）
配置反向代理（Nginx/Traefik）

### 2. 数据备份
```bash
# 备份 PostgreSQL
docker exec langfuse-db pg_dump -U postgres langfuse > backup.sql

# 恢复
docker exec -i langfuse-db psql -U postgres langfuse < backup.sql
```

### 3. 性能优化
- 调整 PostgreSQL 配置
- 增加连接池大小
- 启用 Redis 缓存（可选）

### 4. 扩展追踪范围
当前只追踪 `/qa` 端点的 LLM 调用。未来可以添加：
- 文档提取过程追踪
- 检索性能追踪
- 用户反馈收集

参考: `docs/LANGFUSE_BEST_PRACTICES.md`

## 📚 相关文档

- [完整集成指南](./docs/LANGFUSE_INTEGRATION.md)
- [最佳实践](./docs/LANGFUSE_BEST_PRACTICES.md)
- [快速测试](./TEST_LANGFUSE.md)
- [Langfuse 官方文档](https://langfuse.com/docs)

## 🆘 需要帮助？

如果遇到问题：
1. 查看故障排查部分
2. 运行测试脚本: `python test_langfuse_connection.py`
3. 查看容器日志: `docker logs langfuse-server`
4. 提 Issue 或联系开发者
