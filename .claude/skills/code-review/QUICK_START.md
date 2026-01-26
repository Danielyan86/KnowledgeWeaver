# Code Review Skill - 快速开始

## 基本用法

### 1. 审查单个文件
```bash
/code-review backend/server.py
```

### 2. 审查整个模块
```bash
/code-review backend/
```

### 3. 审查最近的改动
```bash
/code-review --git-diff
```

### 4. 聚焦特定原则
```bash
# 只检查SOLID原则
/code-review backend/server.py --focus=solid

# 只检查安全性
/code-review backend/server.py --focus=security

# 只检查性能
/code-review backend/server.py --focus=performance
```

## 审查流程

1. **代码分析** - 读取并分析代码结构
2. **多维度检查** - 应用8大审查框架
3. **生成报告** - 按严重程度分类问题
4. **运行测试** - 自动执行相关单元测试
5. **提供建议** - 给出具体的改进方案

## 输出示例

```markdown
📊 概览
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
文件: backend/server.py
代码行数: 245 行
整体评级: 良好 ⭐⭐⭐⭐☆

🔴 严重问题 (1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[安全性] server.py:156
问题: API密钥硬编码在代码中
建议: 从环境变量或配置文件读取

🟡 重要建议 (3)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[SRP违背] server.py:89
问题: process_request 函数承担多个职责
建议: 拆分为 validate_request, transform_data, save_result

...

✅ 测试结果
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
运行命令: pytest tests/
结果: 24 passed, 2 failed
覆盖率: 78%
```

## 审查维度

### 🧹 Clean Code
- 命名是否清晰
- 函数是否简洁
- 注释是否必要
- 代码是否DRY

### 🏛️ Clean Architecture
- 分层是否清晰
- 依赖方向是否正确
- 边界是否明确

### 🎯 SOLID
- ✓ 单一职责原则
- ✓ 开闭原则
- ✓ 里氏替换原则
- ✓ 接口隔离原则
- ✓ 依赖倒置原则

### 🎨 设计模式
- 是否正确应用
- 是否过度设计

### ⚡ 性能
- 算法复杂度
- 数据库查询
- 缓存使用

### 🔒 安全性
- 输入验证
- SQL注入
- XSS防护
- 敏感数据处理

### 🧪 测试
- 测试覆盖率
- 测试质量
- 边界测试

### 📐 规范
- 语言规范
- 团队约定
- 格式一致性

## 配置选项

编辑 `config.json` 自定义审查行为：

```json
{
  "defaults": {
    "auto_run_tests": true,
    "max_issues_per_category": 10
  },
  "thresholds": {
    "function_max_lines": 30,
    "function_max_params": 5,
    "max_nesting_depth": 3
  }
}
```

## 常见问题

### Q: 如何跳过测试运行？
A: 在调用时添加 `--skip-tests` 标志（需在skill中实现）

### Q: 如何只看严重问题？
A: 使用 `--severity=critical` 过滤

### Q: 审查结果太多怎么办？
A: 调整 `config.json` 中的 `max_issues_per_category`

### Q: 如何导出报告？
A: 结果会自动显示，可复制保存为markdown文件

## 最佳实践

1. **定期审查** - 在提交代码前运行
2. **增量审查** - 使用 `--git-diff` 只审查改动
3. **优先级** - 先修复严重问题
4. **团队规范** - 根据团队调整配置
5. **持续改进** - 将审查建议融入开发习惯

## 技巧

- 在CI/CD中集成代码审查
- 定期审查核心模块
- 结合静态分析工具（如pylint, eslint）
- 关注测试覆盖率趋势
- 记录并分享审查发现

## 支持的语言

- Python
- JavaScript/TypeScript
- Java
- Go
- C/C++
- 更多语言持续添加...

## 反馈

如果发现审查有误或有改进建议，请修改 `skill.md` 文件。
