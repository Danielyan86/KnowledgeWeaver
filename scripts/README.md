# KnowledgeWeaver Scripts

脚本工具集，用于启动、停止和管理 KnowledgeWeaver 服务。

## 快速开始

### 1. 首次启动（带检查）

```bash
./scripts/start.sh
```

执行完整的启动流程：
- ✅ 检查 Python 环境
- ✅ 检查环境配置文件
- ✅ 检查依赖安装
- ✅ 检查 Neo4j 状态
- ✅ 创建必要目录
- ✅ 检查端口占用
- 🚀 启动服务

### 2. 快速启动（开发模式）

```bash
./scripts/start_dev.sh
```

跳过所有检查，直接启动服务。适合开发时频繁重启。

### 3. 停止服务

```bash
./scripts/stop.sh
```

停止运行中的 KnowledgeWeaver 服务。

### 4. 重启服务

```bash
./scripts/restart.sh
```

等同于执行 `stop.sh` 然后 `start.sh`。

### 5. 查看状态

```bash
./scripts/status.sh
```

显示服务运行状态、访问地址、健康检查结果。

## 脚本说明

### start.sh - 完整启动脚本

**功能**:
- 环境检查（Python、依赖、配置）
- Neo4j 连接检查
- 端口占用检查
- 自动创建必要目录
- 启动服务并显示访问信息
- 支持 Ctrl+C 优雅停止

**适用场景**:
- 首次启动
- 生产环境部署
- 需要完整检查的场景

**输出示例**:
```
======================================================================
🚀 KnowledgeWeaver 启动脚本
======================================================================
ℹ 步骤 1/4: 检查 Python 环境...
✓ Python 版本: 3.11.5
ℹ 步骤 2/4: 检查环境配置...
✓ .env 配置文件存在
ℹ 步骤 3/4: 检查 Python 依赖...
✓ Python 依赖已安装
ℹ 步骤 4/4: 检查 Neo4j 状态...
✓ Neo4j 运行中 (bolt://localhost:7687)
...
======================================================================
📍 服务访问信息
======================================================================
✓ 前端界面:  http://localhost:9621
✓ API 文档:   http://localhost:9621/docs
✓ 健康检查:   http://localhost:9621/health
```

### start_dev.sh - 快速启动脚本

**功能**:
- 跳过所有检查
- 直接启动服务
- 显示访问地址

**适用场景**:
- 开发环境
- 频繁重启
- 已确认环境正常

**输出示例**:
```
======================================================================
🚀 KnowledgeWeaver 快速启动 (开发模式)
======================================================================

✓ 前端界面:  http://localhost:9621
✓ API 文档:   http://localhost:9621/docs

按 Ctrl+C 停止服务
```

### stop.sh - 停止脚本

**功能**:
- 通过 PID 文件停止
- 通过端口查找停止
- 通过进程名停止

**适用场景**:
- 停止服务
- 重启前清理

**输出示例**:
```
停止 KnowledgeWeaver 服务...

✓ 服务已停止 (PID: 12345)
```

### restart.sh - 重启脚本

**功能**:
- 执行 stop.sh
- 等待 2 秒
- 执行 start.sh

**适用场景**:
- 更新配置后重启
- 更新代码后重启

### status.sh - 状态检查脚本

**功能**:
- 检查服务运行状态
- 显示访问地址
- 执行健康检查
- 检查 Neo4j 状态

**适用场景**:
- 查看服务状态
- 故障排查
- 监控服务健康

**输出示例**:
```
======================================================================
📊 KnowledgeWeaver 服务状态
======================================================================

✓ 后端服务运行中 (PID: 12345)

访问地址:
  • 前端界面: http://localhost:9621
  • API 文档:  http://localhost:9621/docs
  • 健康检查: http://localhost:9621/health

ℹ 正在进行健康检查...
✓ 健康检查通过
  响应: {"status":"healthy","timestamp":"2026-01-29T12:34:56"}

✓ Neo4j 运行中 (bolt://localhost:7687)
```

## 其他脚本

### start_with_phoenix.sh

启动服务并启用 Phoenix 追踪（可观测性）。

```bash
./scripts/start_with_phoenix.sh
```

访问 Phoenix UI: http://localhost:6006

### start_phoenix.sh

单独启动 Phoenix 服务。

```bash
./scripts/start_phoenix.sh
```

### test_upload.sh

测试文档上传功能。

```bash
./scripts/test_upload.sh path/to/your/book.txt
```

### run_tests.sh

运行测试套件。

```bash
./scripts/run_tests.sh
```

## 故障排查

### 问题 1: 脚本没有执行权限

**错误**: `Permission denied`

**解决**:
```bash
chmod +x scripts/*.sh
```

### 问题 2: 端口被占用

**错误**: `端口 9621 已被占用！`

**解决方案 1** - 停止占用端口的进程:
```bash
lsof -ti:9621 | xargs kill
```

**解决方案 2** - 修改端口:
编辑 `.env` 文件，修改 `PORT=9621` 为其他端口。

### 问题 3: Neo4j 未运行

**警告**: `Neo4j 未运行`

**解决方案 1** - 启动 Neo4j:
```bash
# Docker
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest

# 本地安装
neo4j start
```

**解决方案 2** - 禁用 Neo4j（使用本地文件存储）:
编辑 `.env` 文件，设置 `USE_NEO4J=false`。

### 问题 4: .env 文件不存在

**错误**: `.env 文件不存在！`

**解决**: 脚本会自动从 `.env.example` 复制，然后需要编辑配置：
```bash
cp .env.example .env
# 编辑 .env，配置 API 密钥和数据库连接
```

### 问题 5: Python 依赖缺失

**错误**: `FastAPI 未安装！`

**解决**:
```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

## 服务访问

启动成功后，可以访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端界面 | http://localhost:9621 | 知识图谱可视化界面 |
| API 文档 | http://localhost:9621/docs | Swagger API 文档 |
| 健康检查 | http://localhost:9621/health | 服务健康状态 |
| Neo4j Browser | http://localhost:7474 | Neo4j 图数据库管理界面 |
| Phoenix UI | http://localhost:6006 | 可观测性追踪界面（如启用） |

## 环境要求

- Python 3.8+
- Neo4j (可选，设置 `USE_NEO4J=false` 可禁用)
- 必需的 Python 包（见 `requirements.txt`）

## 配置说明

关键环境变量（在 `.env` 文件中配置）：

```bash
# 服务配置
HOST=0.0.0.0           # 监听地址
PORT=9621              # 监听端口

# Neo4j 配置
USE_NEO4J=true         # 是否使用 Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# LLM 配置
LLM_BINDING_HOST=https://space.ai-builders.com/backend/v1
LLM_BINDING_API_KEY=your_api_key_here
LLM_MODEL=deepseek

# 提取配置
EXTRACTION_LLM_BACKEND=gemini
GEMINI_API_KEY=your_gemini_api_key_here
```

## 日志和 PID 文件

- **PID 文件**: `logs/server.pid`
- **日志目录**: `logs/`

## 后台运行

如需后台运行服务：

```bash
# 方法 1: nohup
nohup ./scripts/start_dev.sh > logs/server.log 2>&1 &

# 方法 2: screen
screen -S knowledgeweaver
./scripts/start_dev.sh
# Ctrl+A, D 分离会话
# screen -r knowledgeweaver 重新连接

# 方法 3: tmux
tmux new -s knowledgeweaver
./scripts/start_dev.sh
# Ctrl+B, D 分离会话
# tmux attach -t knowledgeweaver 重新连接
```

## 自动启动

### systemd (Linux)

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

[Install]
WantedBy=multi-user.target
```

启用自动启动：
```bash
sudo systemctl enable knowledgeweaver
sudo systemctl start knowledgeweaver
```

### launchd (macOS)

创建 plist 文件 `~/Library/LaunchAgents/com.knowledgeweaver.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
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
</dict>
</plist>
```

加载服务：
```bash
launchctl load ~/Library/LaunchAgents/com.knowledgeweaver.plist
```

---

**更新日期**: 2026-01-29
**维护者**: Sheldon
