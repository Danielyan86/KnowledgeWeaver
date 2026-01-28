# Project Organize Skill

**Name**: project-organize
**Description**: 检查和整理项目结构，确保符合 Clean Architecture 原则
**Version**: 1.0.0
**Author**: Sheldon

## Purpose

自动检查项目目录结构，识别不符合 Clean Architecture 的文件位置，并提供整理建议。确保：
- 根目录保持整洁，只包含必要的配置文件
- 测试文件统一放在 `tests/` 目录
- Docker 配置统一放在 `docker/` 目录
- 文档统一放在 `docs/` 目录
- 工具脚本统一放在 `scripts/` 或 `tools/` 目录

## Usage

```bash
# 检查项目结构（只显示问题）
/project-organize

# 检查并自动整理
/project-organize --fix

# 检查特定目录
/project-organize --path=backend/

# 详细模式（显示所有文件）
/project-organize --verbose
```

## Clean Architecture 目录规范

### 根目录应该包含的文件

✅ **配置文件**：
- `.env.example` - 环境变量示例
- `.gitignore` - Git 忽略规则
- `requirements.txt` / `package.json` - 依赖管理
- `README.md` - 项目说明
- `CLAUDE.md` - Claude Code 配置
- `LICENSE` - 许可证
- `.pylintrc` / `.eslintrc` - 代码检查配置
- `pyproject.toml` / `tsconfig.json` - 构建配置

✅ **必要的脚本**：
- `Makefile` - 常用命令
- `setup.py` / `setup.sh` - 安装脚本

### 根目录不应该包含的文件

❌ **测试文件**（应该在 `tests/` 目录）：
- `test_*.py` / `*.test.js`
- `*_test.py` / `*.spec.js`
- 任何测试相关的脚本

❌ **Docker 文件**（应该在 `docker/` 目录）：
- `docker-compose.*.yml`（除了 `docker-compose.yml` 可以在根目录）
- `Dockerfile.*`（除了主 `Dockerfile`）
- 环境特定的 Docker 配置

❌ **文档文件**（应该在 `docs/` 目录）：
- 技术文档（除了 `README.md`）
- 架构图、设计文档
- API 文档（除非是自动生成的）

❌ **工具脚本**（应该在 `scripts/` 或 `tools/` 目录）：
- 数据迁移脚本
- 部署脚本
- 开发辅助工具

❌ **临时文件**（应该在 `.gitignore`）：
- `.DS_Store` / `Thumbs.db`
- `*.log`
- `*.tmp` / `*.cache`
- IDE 配置（`.vscode/`, `.idea/`）

❌ **源代码文件**（应该在对应的包目录）：
- 业务逻辑代码应该在 `backend/`, `frontend/`, `src/` 等
- 不要在根目录放 `.py`, `.js` 等源代码文件

### 标准项目结构

```
project/
├── backend/              # 后端源代码
│   ├── core/            # 核心模块
│   ├── api/             # API 层
│   ├── models/          # 数据模型
│   └── services/        # 业务服务
├── frontend/            # 前端源代码
├── tests/               # 所有测试文件
│   ├── unit/           # 单元测试
│   ├── integration/    # 集成测试
│   └── data/           # 测试数据
├── docker/              # Docker 配置
│   ├── docker-compose.yml
│   ├── docker-compose.*.yml
│   └── Dockerfile.*
├── docs/                # 文档
│   ├── architecture/   # 架构设计
│   ├── api/            # API 文档
│   └── guides/         # 使用指南
├── scripts/             # 脚本工具
│   ├── deploy.sh
│   ├── migrate.sh
│   └── test.sh
├── data/                # 数据目录（应该在 .gitignore）
├── logs/                # 日志目录（应该在 .gitignore）
├── .env.example         # 环境变量示例
├── .gitignore           # Git 忽略规则
├── README.md            # 项目说明
├── CLAUDE.md            # Claude 配置
└── requirements.txt     # 依赖管理
```

## 检查规则

### 1. 根目录文件检查

对根目录的每个文件，检查是否符合规范：

#### Docker 文件规则
- `docker-compose.yml` - ✅ 可以在根目录
- `Dockerfile` - ✅ 可以在根目录（主 Dockerfile）
- `docker-compose.*.yml` - ❌ 应该在 `docker/` 目录
- `Dockerfile.*` - ❌ 应该在 `docker/` 目录

#### 测试文件规则
- `test_*.py`, `*_test.py` - ❌ 应该在 `tests/` 目录
- `*.test.js`, `*.spec.js` - ❌ 应该在 `tests/` 目录
- `test_*.sh` - ❌ 应该在 `tests/` 或 `scripts/` 目录

#### 文档文件规则
- `README.md` - ✅ 可以在根目录
- `CHANGELOG.md` - ✅ 可以在根目录
- `CONTRIBUTING.md` - ✅ 可以在根目录
- `*.md`（其他） - ❌ 应该在 `docs/` 目录
- `*.png`, `*.jpg`, `*.svg`（图片） - ❌ 应该在 `docs/` 目录

#### 配置文件规则
- `.env` - ❌ 不应该提交（应该在 `.gitignore`）
- `.env.example` - ✅ 可以在根目录
- `config.json` / `config.yaml` - 🟡 根据项目，可能应该在 `config/` 目录

#### 临时文件规则
- `.DS_Store`, `Thumbs.db` - ❌ 应该在 `.gitignore` 并删除
- `*.log` - ❌ 应该在 `.gitignore` 并移动到 `logs/`
- `*.tmp`, `*.cache` - ❌ 应该在 `.gitignore` 并删除

### 2. 目录结构检查

- 是否存在 `tests/` 目录
- 是否存在 `docs/` 目录
- 是否存在 `docker/` 目录（如果有 Docker 配置）
- 是否存在 `scripts/` 或 `tools/` 目录（如果有脚本）

### 3. .gitignore 检查

- 是否忽略了临时文件（`.DS_Store`, `*.log`）
- 是否忽略了环境变量文件（`.env`）
- 是否忽略了数据目录（`data/`, `logs/`）
- 是否忽略了 IDE 配置（`.vscode/`, `.idea/`）

### 4. 敏感信息检查

- Docker Compose 文件是否包含硬编码的密码
- 配置文件是否包含 API Key
- 是否有 `.env` 文件被提交

## 输出格式

### 📊 项目结构检查报告

#### 整体评分
- **结构规范度**: ⭐⭐⭐⭐☆ 4/5
- **安全性**: ⭐⭐⭐☆☆ 3/5
- **可维护性**: ⭐⭐⭐⭐⭐ 5/5

#### 🔴 严重问题 (Critical)
- 敏感信息暴露
- `.env` 文件被提交

#### 🟡 需要整理的文件 (Major)
- 测试文件在根目录
- Docker 配置在根目录
- 文档文件在根目录

#### 🟢 建议优化 (Minor)
- 缺少某些标准目录
- `.gitignore` 规则不完整

#### ✅ 符合规范的部分
- 配置文件位置正确
- 目录结构清晰

### 📝 整理建议

对每个问题文件，提供：
1. **文件位置**：当前路径
2. **问题类型**：为什么不应该在这里
3. **建议位置**：应该移动到哪里
4. **移动命令**：具体的命令（如果 `--fix` 则自动执行）

示例：
```
❌ test_langfuse.py
   问题：测试文件不应该在根目录
   建议：移动到 tests/ 目录
   命令：mv test_langfuse.py tests/
```

### 🎯 优先级

1. **立即处理**：敏感信息、.env 文件
2. **高优先级**：测试文件、Docker 文件
3. **中优先级**：文档文件、脚本文件
4. **低优先级**：临时文件、系统文件

## Implementation Instructions

当 `/project-organize` 被调用时：

### 1. 扫描根目录

```python
# 使用 Glob 工具扫描根目录
files = glob("*")
files += glob(".*")  # 隐藏文件
```

### 2. 分类文件

将文件分类为：
- ✅ 合规文件（应该在根目录）
- ❌ 需要移动的文件
- ⚠️ 可能有问题的文件
- 🗑️ 应该删除的文件（临时文件）

### 3. 检查目录结构

```python
# 检查标准目录是否存在
required_dirs = ["tests/", "docs/", "docker/"]
missing_dirs = []
for dir in required_dirs:
    if not exists(dir):
        missing_dirs.append(dir)
```

### 4. 检查 .gitignore

```python
# 读取 .gitignore 文件
gitignore = read(".gitignore")

# 检查是否包含必要的规则
required_patterns = [
    ".DS_Store",
    "*.log",
    ".env",
    "data/",
    "logs/"
]
missing_patterns = [p for p in required_patterns if p not in gitignore]
```

### 5. 敏感信息扫描

```python
# 扫描 Docker Compose 和配置文件
sensitive_patterns = [
    r"password=.*",
    r"PASSWORD:.*",
    r"api_key=.*",
    r"API_KEY:.*",
    r"secret.*=.*"
]

# 检查文件内容
for file in ["*.yml", "*.yaml", "*.json", ".env"]:
    content = read(file)
    for pattern in sensitive_patterns:
        if re.search(pattern, content):
            flag_as_sensitive(file, pattern)
```

### 6. 生成报告

使用上述输出格式生成报告。

### 7. 执行整理（如果 --fix）

如果用户使用 `--fix` 参数：

```bash
# 创建必要的目录
mkdir -p tests/ docs/ docker/ scripts/

# 移动文件
mv test_*.py tests/
mv docker-compose.*.yml docker/
mv *.md docs/  # 除了 README.md 等

# 删除临时文件
rm -f .DS_Store Thumbs.db

# 更新 .gitignore
echo ".DS_Store" >> .gitignore
```

### 8. 验证结果

整理后，重新运行检查，确认问题已解决。

## 特殊处理

### KnowledgeWeaver 项目特定规则

基于项目的 `CLAUDE.md` 配置：

```python
# 标准目录结构（从 CLAUDE.md 读取）
project_structure = {
    "backend/": "后端源代码",
    "frontend/": "前端源代码",
    "tests/": "所有测试文件",
    "docker/": "Docker 配置",
    "docs/": "文档",
    "scripts/": "脚本工具",
    "data/": "数据目录（.gitignore）",
    "logs/": "日志目录（.gitignore）",
    "tools/": "开发工具"
}

# 项目特定的例外
exceptions = {
    "CLAUDE.md": "项目配置文档，可以在根目录",
    "README.md": "项目说明，可以在根目录",
    "README_CN.md": "中文说明，可以在根目录"
}
```

### 自动化脚本

生成一个 `organize.sh` 脚本供用户运行：

```bash
#!/bin/bash
# 自动整理项目结构

echo "🔧 开始整理项目结构..."

# 创建目录
mkdir -p tests/ docs/ docker/ scripts/

# 移动测试文件
for file in test_*.py; do
    if [ -f "$file" ]; then
        mv "$file" tests/
        echo "✅ 移动 $file -> tests/"
    fi
done

# 移动 Docker 文件
for file in docker-compose.*.yml; do
    if [ -f "$file" ] && [ "$file" != "docker-compose.yml" ]; then
        mv "$file" docker/
        echo "✅ 移动 $file -> docker/"
    fi
done

# 清理临时文件
rm -f .DS_Store
echo "✅ 删除 .DS_Store"

echo "✨ 整理完成！"
```

## Best Practices

1. **谨慎操作**：移动文件前先备份或使用 git
2. **增量整理**：不要一次性改太多，逐步调整
3. **保持沟通**：向用户解释为什么要移动文件
4. **尊重项目**：某些项目可能有特殊的目录结构需求
5. **自动化**：生成脚本让用户可以重复使用

## Examples

### 示例1：基本检查

```bash
/project-organize
```

输出：
```
📊 项目结构检查报告

发现 3 个需要整理的文件：

❌ test_langfuse.py
   问题：测试文件不应该在根目录
   建议：移动到 tests/ 目录

❌ docker-compose.phoenix.yml
   问题：环境特定的 Docker 配置应该在 docker/ 目录
   建议：移动到 docker/ 目录

❌ .DS_Store
   问题：系统临时文件
   建议：删除并添加到 .gitignore

运行 `/project-organize --fix` 自动整理
```

### 示例2：自动整理

```bash
/project-organize --fix
```

输出：
```
🔧 开始整理项目结构...

✅ 移动 test_langfuse.py -> tests/
✅ 移动 docker-compose.phoenix.yml -> docker/
✅ 删除 .DS_Store
✅ 更新 .gitignore

✨ 整理完成！重新检查...

📊 项目结构检查报告

✅ 所有文件位置正确
✅ 目录结构符合规范
✅ .gitignore 配置完善

项目结构规范度：⭐⭐⭐⭐⭐ 5/5
```

## Notes

- 每次整理后建议运行测试，确保路径引用没有问题
- 对于大型项目，建议分批整理
- 整理前确保代码已提交到 git，方便回滚
- 某些框架（如 Next.js, Django）可能有自己的目录约定
- 整理后需要更新文档中的路径引用
