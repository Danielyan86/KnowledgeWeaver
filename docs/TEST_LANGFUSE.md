# Langfuse 快速测试指南

## ⚡ 5 分钟完成测试

### 1️⃣ 安装依赖（30秒）
```bash
pip install langfuse>=2.0.0
```

### 2️⃣ 注册 Langfuse Cloud（2分钟）
1. 访问: https://cloud.langfuse.com
2. 注册免费账号
3. 创建项目
4. 复制 Public Key 和 Secret Key

### 3️⃣ 配置环境变量（1分钟）
编辑 `.env` 文件，添加：
```bash
# Langfuse Configuration
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-你的公钥
LANGFUSE_SECRET_KEY=sk-lf-你的密钥
LANGFUSE_HOST=https://cloud.langfuse.com
```

### 4️⃣ 启动服务（10秒）
```bash
python -m backend.server
```

看到这行说明集成成功：
```
✅ Langfuse 已启用: cloud
✅ OpenAI 客户端已包装 Langfuse 追踪
```

### 5️⃣ 发送测试请求（30秒）
```bash
curl -X POST http://localhost:9621/qa \
  -H "Content-Type: application/json" \
  -d '{
    "question": "什么是知识图谱？",
    "mode": "auto"
  }'
```

### 6️⃣ 查看追踪数据（1分钟）
1. 访问 https://cloud.langfuse.com
2. 点击 "Traces" 标签
3. 看到刚才的请求！

应该能看到：
- ✅ 用户问题
- ✅ 生成的答案
- ✅ LLM 调用详情
- ✅ Token 使用量
- ✅ 执行时间
- ✅ 成本

## 🎉 成功！

你已经完成了集成，现在每次调用 `/qa` API 都会自动追踪到 Langfuse。

## 📊 查看更多

- **Token 统计**: Dashboard 首页
- **成本分析**: Dashboard → Usage
- **慢查询**: Traces → 按延迟排序
- **错误追踪**: Traces → 筛选 error

## 🔧 故障排查

### 看不到追踪数据？

1. 检查服务启动日志是否有 "✅ Langfuse 已启用"
2. 确认 `.env` 中 `LANGFUSE_ENABLED=true`
3. 确认 API Keys 正确
4. 等待 5-10 秒刷新 Dashboard（数据是异步发送的）

### 想要禁用？

```bash
# .env
LANGFUSE_ENABLED=false
```

重启服务即可。

## 📚 下一步

查看详细文档了解更多功能：

- [完整指南](./LANGFUSE_GUIDE.md) - 包含集成方案、最佳实践和自托管部署
