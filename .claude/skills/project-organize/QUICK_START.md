# Project Organize Skill - 快速入门

## 简介

这个 skill 用于检查和整理项目结构，确保符合 Clean Architecture 原则。

## 快速使用

### 基本检查

```bash
/project-organize
```

这会扫描项目根目录，列出所有不符合规范的文件。

### 自动整理

```bash
/project-organize --fix
```

自动将文件移动到正确的位置。

### 详细模式

```bash
/project-organize --verbose
```

显示所有文件，包括符合规范的文件。

## 常见问题

### Q: 会移动哪些文件？

A: 主要移动以下类型的文件：
- 测试文件（`test_*.py`）-> `tests/`
- Docker 配置（`docker-compose.*.yml`）-> `docker/`
- 文档文件（`*.md` 除了 README 等）-> `docs/`
- 临时文件（`.DS_Store`）-> 删除

### Q: 会不会误删重要文件？

A: 不会。skill 只会：
1. 检查模式默认只显示问题，不做任何修改
2. `--fix` 模式会先询问确认
3. 永远不会删除源代码文件
4. 建议在使用前先提交 git，方便回滚

### Q: 根目录应该放什么？

A: 只应该放：
- 配置文件（`.env.example`, `requirements.txt`, `.gitignore`）
- 主要文档（`README.md`, `LICENSE`）
- 主 Dockerfile（`Dockerfile`, `docker-compose.yml`）
- 构建文件（`Makefile`, `setup.py`）

### Q: 如何添加例外？

A: 编辑 `config.json` 中的 `exceptions` 字段。

## 示例输出

```
📊 项目结构检查报告

整体评分: ⭐⭐⭐⭐☆ 4/5

🔴 严重问题 (0)
   无

🟡 需要整理的文件 (3)
   ❌ test_langfuse.py
      问题：测试文件不应该在根目录
      建议：移动到 tests/
      命令：mv test_langfuse.py tests/

   ❌ docker-compose.phoenix.yml
      问题：环境特定的 Docker 配置
      建议：移动到 docker/
      命令：mv docker-compose.phoenix.yml docker/

   ❌ .DS_Store
      问题：系统临时文件
      建议：删除
      命令：rm .DS_Store

🟢 建议优化 (1)
   ⚠️ .gitignore 缺少规则：.DS_Store

✅ 符合规范 (15 个文件)
   ✓ README.md
   ✓ requirements.txt
   ✓ .gitignore
   ...

运行 `/project-organize --fix` 自动整理
```

## 工作流程

1. **定期检查**：在提交代码前运行检查
2. **新增文件**：添加新文件时，确保放在正确位置
3. **清理临时文件**：定期运行 `--fix` 清理系统文件
4. **更新 .gitignore**：根据建议更新忽略规则

## 自定义配置

编辑 `.claude/skills/project-organize/config.json` 可以自定义：

- 允许在根目录的文件类型
- 需要移动的文件模式
- 敏感信息检测规则
- 标准目录结构

## 集成到工作流

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "🔍 检查项目结构..."
claude /project-organize
if [ $? -ne 0 ]; then
    echo "❌ 项目结构检查失败，请整理后再提交"
    exit 1
fi
```

### CI/CD

```yaml
# .github/workflows/structure-check.yml
name: Structure Check
on: [push, pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Check project structure
        run: claude /project-organize
```

## 最佳实践

1. **提交前检查**：养成提交前运行检查的习惯
2. **分批整理**：大项目不要一次性改太多
3. **更新文档**：整理后更新文档中的路径
4. **测试验证**：移动文件后运行测试，确保导入路径正确
5. **团队约定**：与团队统一目录结构规范

## 相关 Skills

- `/code-review` - 代码质量审查
- `/commit` - 提交代码（会自动检查结构）

## 反馈

如有问题或建议，请联系 Sheldon 或提交 Issue。
