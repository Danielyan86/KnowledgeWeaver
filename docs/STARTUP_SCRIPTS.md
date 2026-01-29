# Startup Scripts Documentation

启动脚本完整文档

## 概述

KnowledgeWeaver 提供了一套完整的启动、停止和管理脚本，简化服务的运维操作。

## 脚本列表

| 脚本 | 功能 | 适用场景 |
|------|------|----------|
| `start.sh` | 完整启动（带检查） | 首次启动、生产环境 |
| `start_dev.sh` | 快速启动（开发模式） | 开发环境、频繁重启 |
| `stop.sh` | 停止服务 | 停止运行中的服务 |
| `restart.sh` | 重启服务 | 更新配置/代码后重启 |
| `status.sh` | 状态检查 | 查看服务状态、故障排查 |

## 快速使用

### 首次启动

```bash
# 1. 确保脚本有执行权限
chmod +x scripts/*.sh

# 2. 启动服务（带完整检查）
./scripts/start.sh
```

### 日常开发

```bash
# 快速启动
./scripts/start_dev.sh

# 查看状态
./scripts/status.sh

# 停止服务
./scripts/stop.sh

# 重启服务
./scripts/restart.sh
```

## 脚本详解

### 1. start.sh - 完整启动脚本

**执行流程**:
```
检查 Python 环境
    ↓
检查 .env 配置
    ↓
检查 Python 依赖
    ↓
检查 Neo4j 状态
    ↓
创建必要目录
    ↓
检查端口占用
    ↓
启动服务
    ↓
显示访问信息
```

**优点**:
- ✅ 完整的环境检查
- ✅ 友好的错误提示
- ✅ 自动创建目录
- ✅ 支持 Ctrl+C 优雅停止

**使用示例**:
```bash
./scripts/start.sh

# 输出示例：
# ====================================================================
# 🚀 KnowledgeWeaver 启动脚本
# ====================================================================
# ℹ 步骤 1/4: 检查 Python 环境...
# ✓ Python 版本: 3.11.5
# ...
# ✓ 前端界面:  http://localhost:9621
```

### 2. start_dev.sh - 快速启动脚本

**特点**:
- 跳过所有检查
- 直接启动服务
- 输出简洁

**使用示例**:
```bash
./scripts/start_dev.sh

# 输出：
# 🚀 KnowledgeWeaver 快速启动 (开发模式)
# ✓ 前端界面:  http://localhost:9621
# ✓ API 文档:   http://localhost:9621/docs
```

### 3. stop.sh - 停止脚本

**停止策略**（按顺序尝试）:
1. 通过 PID 文件停止
2. 通过端口查找停止
3. 通过进程名停止

**使用示例**:
```bash
./scripts/stop.sh

# 输出：
# 停止 KnowledgeWeaver 服务...
# ✓ 服务已停止 (PID: 12345)
```

### 4. restart.sh - 重启脚本

**执行逻辑**:
```bash
stop.sh
    ↓
sleep 2
    ↓
start.sh
```

**使用场景**:
- 修改配置后需要重启
- 更新代码后需要重启
- 服务异常需要重启

### 5. status.sh - 状态检查脚本

**检查内容**:
- ✅ 服务运行状态
- ✅ 进程 PID
- ✅ 访问地址
- ✅ 健康检查
- ✅ Neo4j 状态

**使用示例**:
```bash
./scripts/status.sh

# 输出：
# 📊 KnowledgeWeaver 服务状态
# ✓ 后端服务运行中 (PID: 12345)
#
# 访问地址:
#   • 前端界面: http://localhost:9621
#   • API 文档:  http://localhost:9621/docs
#   • 健康检查: http://localhost:9621/health
#
# ✓ 健康检查通过
# ✓ Neo4j 运行中 (bolt://localhost:7687)
```

## 服务架构

KnowledgeWeaver 采用**单一服务架构**，后端 FastAPI 服务同时提供：
1. RESTful API 端点
2. 前端静态文件服务
3. WebSocket 支持（如需要）

```
┌─────────────────────────────────────┐
│   FastAPI Backend (Port 9621)      │
│                                     │
│  ┌─────────────┐  ┌──────────────┐ │
│  │   API       │  │   Frontend   │ │
│  │  Endpoints  │  │  Static      │ │
│  │             │  │  Files       │ │
│  └─────────────┘  └──────────────┘ │
│                                     │
│  ┌─────────────┐  ┌──────────────┐ │
│  │   Neo4j     │  │   ChromaDB   │ │
│  │  (External) │  │   (Embedded) │ │
│  └─────────────┘  └──────────────┘ │
└─────────────────────────────────────┘
```

因此，只需启动一个服务即可同时访问前端和后端。

## 配置要求

### 必需配置

在 `.env` 文件中必须配置：

```bash
# LLM API（问答系统）
LLM_BINDING_HOST=https://space.ai-builders.com/backend/v1
LLM_BINDING_API_KEY=your_api_key_here

# 提取 LLM（文档处理）
EXTRACTION_LLM_BACKEND=gemini
GEMINI_API_KEY=your_gemini_api_key_here
```

### 可选配置

```bash
# Neo4j（可选，可设置为 false 使用本地文件存储）
USE_NEO4J=true
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# 服务端口（可选，默认 9621）
PORT=9621
HOST=0.0.0.0
```

## 故障排查

### 问题 1: 权限错误

**错误**: `Permission denied`

**原因**: 脚本没有执行权限

**解决**:
```bash
chmod +x scripts/*.sh
```

### 问题 2: 端口被占用

**错误**: `端口 9621 已被占用！`

**解决方案 1** - 停止占用端口的进程:
```bash
# 查找占用端口的进程
lsof -ti:9621

# 停止进程
lsof -ti:9621 | xargs kill
```

**解决方案 2** - 修改端口:
```bash
# 编辑 .env 文件
PORT=9622
```

### 问题 3: Python 环境问题

**错误**: `Python 未安装` 或 `FastAPI 未安装`

**解决**:
```bash
# 检查 Python 版本
python --version  # 需要 3.8+

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 问题 4: Neo4j 未运行

**警告**: `Neo4j 未运行`

**解决方案 1** - 启动 Neo4j (Docker):
```bash
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

**解决方案 2** - 禁用 Neo4j:
```bash
# 编辑 .env 文件
USE_NEO4J=false
```

### 问题 5: .env 文件缺失

**错误**: `.env 文件不存在！`

**解决**: 脚本会自动复制模板，然后需要编辑：
```bash
# 脚本自动执行：
cp .env.example .env

# 然后编辑配置
nano .env  # 或使用其他编辑器
```

### 问题 6: 服务启动但无法访问

**检查步骤**:
```bash
# 1. 检查服务状态
./scripts/status.sh

# 2. 检查健康检查端点
curl http://localhost:9621/health

# 3. 查看日志
tail -f logs/server.log  # 如果有日志文件

# 4. 检查防火墙
# Linux
sudo ufw status
# macOS - 系统偏好设置 > 安全性与隐私 > 防火墙
```

## 高级用法

### 后台运行

**方法 1: nohup**
```bash
nohup ./scripts/start_dev.sh > logs/server.log 2>&1 &
echo $! > logs/server.pid
```

**方法 2: screen**
```bash
screen -S knowledgeweaver
./scripts/start_dev.sh
# Ctrl+A, D 分离
# screen -r knowledgeweaver 重新连接
```

**方法 3: tmux**
```bash
tmux new -s knowledgeweaver
./scripts/start_dev.sh
# Ctrl+B, D 分离
# tmux attach -t knowledgeweaver 重新连接
```

### 自动重启

**使用 systemd (Linux)**:

创建服务文件 `/etc/systemd/system/knowledgeweaver.service`:
```ini
[Unit]
Description=KnowledgeWeaver Service
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/KnowledgeWeaver
ExecStart=/path/to/KnowledgeWeaver/scripts/start_dev.sh
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

启用和启动：
```bash
sudo systemctl enable knowledgeweaver
sudo systemctl start knowledgeweaver
sudo systemctl status knowledgeweaver
```

**使用 launchd (macOS)**:

创建 `~/Library/LaunchAgents/com.knowledgeweaver.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.knowledgeweaver</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/KnowledgeWeaver/scripts/start_dev.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/path/to/KnowledgeWeaver/logs/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/KnowledgeWeaver/logs/stderr.log</string>
</dict>
</plist>
```

加载：
```bash
launchctl load ~/Library/LaunchAgents/com.knowledgeweaver.plist
launchctl start com.knowledgeweaver
```

### 多环境管理

**使用不同的 .env 文件**:
```bash
# 开发环境
cp .env.dev .env
./scripts/start_dev.sh

# 生产环境
cp .env.prod .env
./scripts/start.sh
```

**使用不同的端口**:
```bash
# .env.dev
PORT=9621

# .env.prod
PORT=9622
```

## 监控和日志

### 实时监控

```bash
# 监控服务状态（每 5 秒刷新）
watch -n 5 ./scripts/status.sh

# 监控健康检查
watch -n 5 'curl -s http://localhost:9621/health | jq'
```

### 日志管理

```bash
# 查看实时日志（如果有）
tail -f logs/server.log

# 查看最近 100 行日志
tail -n 100 logs/server.log

# 搜索错误日志
grep ERROR logs/server.log
```

## 最佳实践

### 开发环境

```bash
# 1. 使用虚拟环境
python -m venv venv
source venv/bin/activate

# 2. 使用快速启动
./scripts/start_dev.sh

# 3. 修改代码后重启
./scripts/restart.sh
```

### 生产环境

```bash
# 1. 使用完整启动脚本
./scripts/start.sh

# 2. 配置系统服务自动启动
sudo systemctl enable knowledgeweaver

# 3. 定期检查服务状态
./scripts/status.sh

# 4. 设置监控告警
watch -n 60 './scripts/status.sh | mail -s "KW Status" admin@example.com'
```

## 总结

启动脚本提供了：
- ✅ **简化操作**: 一键启动/停止/重启
- ✅ **环境检查**: 自动检测配置和依赖
- ✅ **友好提示**: 清晰的错误信息和解决方案
- ✅ **状态监控**: 实时查看服务状态和健康状况
- ✅ **灵活性**: 支持开发和生产环境

---

**更新日期**: 2026-01-29
**维护者**: Sheldon
**版本**: 2.1.0
