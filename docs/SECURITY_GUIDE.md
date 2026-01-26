# KnowledgeWeaver 安全指南

## 🔐 安全配置清单

### 1. 环境变量管理

#### ✅ 正确做法

**步骤 1：创建 .env 文件**
```bash
# 复制示例文件
cp .env.example .env

# 编辑并填入真实值
vim .env
```

**步骤 2：填写安全的配置**
```bash
# 生成安全的密钥（32+ 字符）
LANGFUSE_NEXTAUTH_SECRET=$(openssl rand -base64 32)
LANGFUSE_SALT=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 16)
NEO4J_PASSWORD=$(openssl rand -base64 16)
```

**步骤 3：确保 .env 被忽略**
```bash
# 检查 .gitignore
cat .gitignore | grep .env

# 应该看到：
# .env
# .env.local
# .env.*.local
```

#### ❌ 错误做法

```yaml
# ❌ 不要在 Docker Compose 中硬编码密码
environment:
  - DATABASE_URL=postgresql://postgres:postgres@db:5432/langfuse
  - NEXTAUTH_SECRET=mysecretkey123456789
  - SALT=mysalt123456789
```

```python
# ❌ 不要在代码中硬编码 API 密钥
api_key = "sk-1234567890abcdef"
```

### 2. Docker Compose 安全配置

#### ✅ 正确配置

**docker-compose.langfuse.yml:**
```yaml
version: '3.8'

services:
  langfuse-server:
    environment:
      # 从环境变量读取
      - DATABASE_URL=${LANGFUSE_DATABASE_URL}
      - NEXTAUTH_SECRET=${LANGFUSE_NEXTAUTH_SECRET}
      - SALT=${LANGFUSE_SALT}

  langfuse-db:
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
```

**使用方法：**
```bash
# 1. 确保 .env 文件存在并包含必要变量
# 2. 启动服务
docker-compose -f docker-compose.langfuse.yml up -d
```

### 3. Git 提交安全

#### 当前保护机制

项目已配置 Git hooks 来检测敏感信息：

```bash
# 提交时自动检测
git commit -m "your message"

# 如果检测到敏感信息：
❌ SENSITIVE INFORMATION DETECTED!

📄 docker-compose.langfuse.yml
  Line 13: Database Connection String
    - DATABASE_URL=postgresql://postgres:postgres@...
```

#### 修复步骤

1. **更新文件使用环境变量**
   ```yaml
   # 将硬编码密码改为环境变量
   - DATABASE_URL=${LANGFUSE_DATABASE_URL}
   ```

2. **将敏感值移到 .env**
   ```bash
   echo "LANGFUSE_DATABASE_URL=postgresql://postgres:secure_password@db:5432/langfuse" >> .env
   ```

3. **再次提交**
   ```bash
   git add .
   git commit -m "Fix: Use environment variables for sensitive data"
   ```

### 4. 敏感文件清单

#### 必须忽略的文件

```gitignore
# 环境变量
.env
.env.local
.env.*.local

# 包含密码的 Docker Compose
docker-compose.override.yml
docker-compose.langfuse.yml  # 如果包含硬编码密码

# 数据库文件
*.db
*.sqlite3

# 日志文件（可能包含敏感信息）
logs/*.log

# 缓存（可能包含 API 响应）
data/cache/
```

#### 可以提交的文件

```
✅ .env.example                    # 示例配置（不含真实值）
✅ docker-compose.*.example.yml    # 示例配置
✅ .gitignore                      # Git 忽略规则
✅ requirements.txt                # 依赖列表
```

## 🛡️ 安全最佳实践

### 1. 密码强度

#### 生成强密码

```bash
# 方法 1: OpenSSL（推荐）
openssl rand -base64 32

# 方法 2: Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 方法 3: pwgen
pwgen -s 32 1
```

#### 密码要求

| 类型 | 最小长度 | 建议长度 |
|------|---------|---------|
| 数据库密码 | 16 字符 | 32 字符 |
| API 密钥 | 32 字符 | 64 字符 |
| JWT Secret | 32 字符 | 64 字符 |
| Salt | 16 字符 | 32 字符 |

### 2. API 密钥管理

#### ✅ 正确做法

```python
# 从环境变量读取
import os
api_key = os.getenv('LLM_BINDING_API_KEY')

if not api_key:
    raise ValueError("LLM_BINDING_API_KEY not set")
```

#### ❌ 错误做法

```python
# 硬编码（绝对不要这样做）
api_key = "sk-1234567890abcdef"
```

### 3. 数据库连接

#### ✅ 正确做法

```python
# 使用环境变量
from dotenv import load_dotenv
load_dotenv()

db_url = os.getenv('NEO4J_URI')
db_user = os.getenv('NEO4J_USER')
db_password = os.getenv('NEO4J_PASSWORD')
```

#### ❌ 错误做法

```python
# 硬编码连接字符串
db_url = "bolt://neo4j:password@localhost:7687"
```

### 4. 日志安全

#### ✅ 正确做法

```python
import logging

# 脱敏敏感信息
def sanitize_log(message):
    # 移除密码、API 密钥等
    import re
    message = re.sub(r'password=[^&\s]+', 'password=***', message)
    message = re.sub(r'api_key=[^&\s]+', 'api_key=***', message)
    return message

logging.info(sanitize_log(f"Connecting to {db_url}"))
```

#### ❌ 错误做法

```python
# 直接记录敏感信息
logging.info(f"Connecting to {db_url} with password {password}")
```

## 🔍 安全检查工具

### 1. Git Hooks

项目已配置 pre-commit hooks 检测敏感信息。

**位置：** `tools/hooks/pre-commit`

**检测规则：**
- 数据库连接字符串
- API 密钥
- 密码
- Secret 密钥
- 私钥文件

### 2. 手动检查

```bash
# 检查是否有敏感信息
grep -r "password" . --include="*.yml" --include="*.yaml"
grep -r "api_key" . --include="*.py"
grep -r "secret" . --include="*.env"

# 检查 Git 历史（查找已提交的敏感信息）
git log -p | grep -i "password"
```

### 3. 第三方工具

```bash
# 安装 git-secrets
brew install git-secrets  # macOS
apt-get install git-secrets  # Ubuntu

# 配置
git secrets --install
git secrets --register-aws

# 扫描
git secrets --scan
```

## 🚨 紧急响应

### 如果不小心提交了敏感信息

#### 步骤 1: 立即更改密码/密钥

```bash
# 更改所有受影响的密码和密钥
# 例如：重新生成 API 密钥、更改数据库密码
```

#### 步骤 2: 从 Git 历史中删除

```bash
# 使用 BFG Repo-Cleaner（推荐）
bfg --replace-text passwords.txt

# 或使用 git filter-branch
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch path/to/sensitive/file" \
  --prune-empty --tag-name-filter cat -- --all

# 强制推送（警告：会覆盖远程历史）
git push --force --all
git push --force --tags
```

#### 步骤 3: 通知相关人员

- 通知团队成员
- 如果是公开仓库，发布安全公告
- 监控异常访问

## 📋 安全检查清单

### 开发前

- [ ] 复制 `.env.example` 为 `.env`
- [ ] 生成强密码和密钥
- [ ] 确认 `.env` 在 `.gitignore` 中
- [ ] 配置 Git hooks

### 开发中

- [ ] 所有密码使用环境变量
- [ ] API 密钥从环境变量读取
- [ ] 日志中脱敏敏感信息
- [ ] 不在代码中硬编码配置

### 提交前

- [ ] 检查 Git status（确保不包含 .env）
- [ ] 运行 `git secrets --scan`
- [ ] 审查 diff（`git diff --cached`）
- [ ] 确认 hooks 正常工作

### 部署前

- [ ] 更改所有默认密码
- [ ] 使用强密码（32+ 字符）
- [ ] 启用 HTTPS
- [ ] 配置防火墙
- [ ] 限制数据库访问
- [ ] 配置 CORS 白名单

### 定期检查

- [ ] 每月审查访问日志
- [ ] 每季度更新密码
- [ ] 检查依赖包安全更新
- [ ] 审计第三方服务权限

## 🔗 相关资源

### 工具

- [git-secrets](https://github.com/awslabs/git-secrets) - 防止提交密码
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/) - 清理 Git 历史
- [truffleHog](https://github.com/trufflesecurity/truffleHog) - 扫描密钥
- [detect-secrets](https://github.com/Yelp/detect-secrets) - 密钥检测

### 最佳实践

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)

## 📞 报告安全问题

如果发现安全漏洞，请：

1. **不要公开披露**
2. 联系维护者：Sheldon
3. 提供详细信息：
   - 问题描述
   - 影响范围
   - 复现步骤
   - 建议修复方案

---

**最后更新：** 2026-01-26
**版本：** 1.0.0
