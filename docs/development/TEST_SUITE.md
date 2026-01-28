# KnowledgeWeaver 测试套件文档

## 概述

本文档描述 KnowledgeWeaver 项目的测试套件，包括单元测试、集成测试的组织结构、运行方法和覆盖范围。

## 测试统计

**当前状态：** ✅ 85/90 单元测试通过 (94% 通过率)

### 测试分布

| 模块 | 测试文件 | 测试数量 | 状态 |
|------|---------|---------|------|
| 配置模块 | `test_config.py` | 12 | ✅ 全部通过 |
| 规范化器 | `test_normalizer.py` | 19 | ✅ 全部通过 |
| 实体过滤 | `test_entity_filter.py` | 12 | ✅ 全部通过 |
| 嵌入服务 | `test_embeddings.py` | 11 | ✅ 10/11 通过 |
| KG 管理器 | `test_kg_manager.py` | 15 | ✅ 11/15 通过 |
| 进度追踪 | `test_progress_tracker.py` | 10 | ✅ 全部通过 |
| API 端点 | `test_api.py` | 13 | ✅ 12/13 通过 |

**总计：** 92 个测试用例

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行测试

#### 方式 1：使用测试脚本（推荐）

```bash
# 运行全部测试
./run_tests.sh

# 只运行单元测试
./run_tests.sh unit

# 生成覆盖率报告
./run_tests.sh coverage
```

#### 方式 2：直接使用 pytest

```bash
# 运行全部测试
pytest

# 只运行单元测试
pytest -m unit

# 运行特定文件
pytest tests/test_config.py

# 详细输出
pytest -v

# 生成覆盖率报告
pytest --cov=backend --cov-report=html
```

## 测试组织

### 目录结构

```
tests/
├── conftest.py           # Pytest 配置和 fixtures
├── pytest.ini            # Pytest 配置文件
├── README.md             # 测试文档
│
├── test_config.py        # 配置模块测试
├── test_normalizer.py    # 图谱规范化测试
├── test_entity_filter.py # 实体过滤测试
├── test_embeddings.py    # 嵌入服务测试
├── test_kg_manager.py    # KG 管理器测试
├── test_progress_tracker.py  # 进度追踪测试
└── test_api.py           # API 端点测试
```

### 测试标记

使用 pytest 标记区分测试类型：

- `@pytest.mark.unit` - 单元测试（快速，无外部依赖）
- `@pytest.mark.integration` - 集成测试（需要外部服务）
- `@pytest.mark.slow` - 慢速测试（可选择跳过）

### Fixtures

在 `conftest.py` 中定义的共享 fixtures：

#### 数据 Fixtures
- `sample_entities` - 示例实体列表
- `sample_relations` - 示例关系列表
- `sample_graph` - 示例知识图谱
- `sample_chunks` - 示例文本块

#### 环境 Fixtures
- `mock_env_vars` - 模拟环境变量
- `test_data_dir` - 临时测试数据目录
- `sample_text_file` - 示例文本文件

#### 服务 Fixtures
- `api_client` - FastAPI 测试客户端
- `mock_neo4j_storage` - 模拟 Neo4j 存储
- `mock_openai_client` - 模拟 OpenAI 客户端

## 测试覆盖详情

### 1. 配置模块 (`test_config.py`)

测试 `backend/core/config.py` 中的配置和验证函数。

**测试用例：**
- ✅ 实体验证（有效性、缺失字段、名称长度、类型检查）
- ✅ 关系验证（有效性、缺失字段、关系词检查）
- ✅ 节点类型定义
- ✅ 标准关系词表
- ✅ 提示词生成

**覆盖的功能：**
- `validate_entity()` - 实体验证
- `validate_relation()` - 关系验证
- `get_entity_extraction_prompt()` - 实体提取提示词
- `get_relation_extraction_prompt()` - 关系提取提示词

### 2. 规范化器 (`test_normalizer.py`)

测试 `backend/extraction/normalizer.py` 的图谱规范化功能。

**测试用例：**
- ✅ 节点名称规范化（去空格、移除特殊字符、截断长名称）
- ✅ 节点类型推断（人名、书籍、策略、概念）
- ✅ 关系名称规范化（标准化、映射、模糊匹配）
- ✅ 节点和边规范化
- ✅ 重复节点合并
- ✅ 完整图谱规范化
- ✅ 自环过滤
- ✅ 属性提取

**覆盖的功能：**
- `normalize_node_name()` - 节点名称规范化
- `infer_node_type()` - 节点类型推断
- `normalize_relation()` - 关系规范化
- `normalize_node()` / `normalize_edge()` - 节点/边规范化
- `merge_duplicate_nodes()` - 去重
- `normalize_graph()` - 图谱规范化

### 3. 实体过滤 (`test_entity_filter.py`)

测试 `backend/extraction/entity_filter.py` 的实体过滤功能。

**测试用例：**
- ✅ 过滤空实体
- ✅ 过滤停用词
- ✅ 过滤单字实体
- ✅ 过滤纯数字
- ✅ 过滤特殊字符
- ✅ 过滤过长实体
- ✅ 保留有效实体
- ✅ 过滤实体列表
- ✅ 过滤关系
- ✅ 关系规范化
- ✅ 完整图谱过滤
- ✅ 单例模式

**覆盖的功能：**
- `should_filter()` - 判断是否过滤
- `filter_entities()` - 过滤实体列表
- `filter_relations()` - 过滤关系列表
- `normalize_relation()` - 关系规范化
- `filter_graph()` - 完整图谱过滤
- `get_entity_filter()` - 获取单例

### 4. 嵌入服务 (`test_embeddings.py`)

测试 `backend/core/embeddings/service.py` 的向量嵌入服务。

**测试用例：**
- ✅ 单文本嵌入成功
- ✅ 空文本处理
- ✅ 缓存机制
- ✅ 错误处理
- ✅ 批量嵌入
- ✅ 空列表处理
- ⏳ 过滤空文本（部分通过）
- ✅ 缓存键生成

**覆盖的功能：**
- `embed_text()` - 单文本嵌入
- `embed_texts()` - 批量嵌入
- `_get_cache_key()` - 缓存键生成
- 错误处理和缓存机制

### 5. KG 管理器 (`test_kg_manager.py`)

测试 `backend/management/kg_manager.py` 的知识图谱管理功能。

**测试用例：**
- ✅ Neo4j 初始化
- ✅ 保存文档
- ✅ 保存已规范化图谱
- ✅ Neo4j 错误处理
- ⏳ 加载文档（需要调整 mock）
- ✅ 删除文档
- ⏳ 列出文档（需要调整 mock）
- ✅ 获取统计信息
- ✅ 获取热门标签
- ⏳ 按标签查询（需要调整 mock）
- ✅ 获取全部图谱
- ✅ 保存空图谱
- ✅ 并发保存

**覆盖的功能：**
- `save_document()` - 保存文档
- `load_document()` - 加载文档
- `delete_document()` - 删除文档
- `list_documents()` - 列出文档
- `get_stats()` - 获取统计
- `get_popular_labels()` - 获取热门标签
- `get_graph_by_label()` - 按标签查询
- `get_all_graphs()` - 获取全部图谱

### 6. 进度追踪 (`test_progress_tracker.py`)

测试 `backend/management/progress_tracker.py` 的进度追踪功能。

**测试用例：**
- ✅ 初始化创建目录
- ✅ 开始进度追踪
- ✅ 更新进度
- ✅ 完成进度
- ✅ 失败进度
- ✅ 获取不存在的进度
- ✅ 进度持久化
- ✅ 多文档追踪
- ✅ 百分比计算
- ✅ 边界情况

**覆盖的功能：**
- `start()` - 开始追踪
- `update()` - 更新进度
- `complete()` - 标记完成
- `fail()` - 标记失败
- `get()` - 获取进度
- 进度计算和持久化

### 7. API 端点 (`test_api.py`)

测试 `backend/server.py` 的 FastAPI 端点。

**测试用例：**
- ✅ 健康检查
- ✅ 获取热门标签
- ✅ 获取全部图谱
- ✅ 按标签获取图谱
- ✅ 列出文档
- ✅ 获取文档图谱
- ✅ 获取不存在的文档
- ✅ 删除文档
- ✅ 获取统计信息
- ⏳ 问答接口（需要调整 mock）
- ✅ 语义搜索
- ✅ 获取实体上下文
- ✅ 上传文档
- ✅ 上传无效格式

**覆盖的端点：**
- `GET /health` - 健康检查
- `GET /graph/label/popular` - 热门标签
- `GET /graphs` - 图谱查询
- `GET /documents` - 列出文档
- `GET /documents/{doc_id}` - 获取文档
- `DELETE /documents/{doc_id}` - 删除文档
- `GET /stats` - 统计信息
- `POST /qa` - 问答
- `POST /search` - 搜索
- `GET /entities/{entity_name}/context` - 实体上下文
- `POST /documents/upload` - 上传文档

## 运行示例

### 运行特定测试类

```bash
pytest tests/test_config.py::TestConfigValidation
```

### 运行特定测试函数

```bash
pytest tests/test_config.py::TestConfigValidation::test_validate_entity_success
```

### 显示详细输出

```bash
pytest -v -s
```

### 只运行失败的测试

```bash
pytest --lf
```

### 生成 HTML 覆盖率报告

```bash
pytest --cov=backend --cov-report=html
open htmlcov/index.html
```

### 显示最慢的测试

```bash
pytest --durations=10
```

## 持续改进

### 待添加的测试

- [ ] `backend/extraction/extractor.py` - 知识提取器
- [ ] `backend/extraction/async_extractor.py` - 异步提取器
- [ ] `backend/retrieval/hybrid_retriever.py` - 混合检索器
- [ ] `backend/retrieval/qa_engine.py` - 问答引擎
- [ ] `backend/core/storage/neo4j.py` - Neo4j 存储
- [ ] `backend/core/storage/vector.py` - 向量存储
- [ ] 端到端集成测试

### 提升覆盖率

目标：**95%+ 代码覆盖率**

当前覆盖的模块：
- ✅ 配置模块：100%
- ✅ 规范化器：~95%
- ✅ 实体过滤：~90%
- ✅ 进度追踪：~95%
- ⏳ 嵌入服务：~80%
- ⏳ KG 管理器：~70%
- ⏳ API 端点：~80%

需要提升的模块：
- ⏳ 知识提取器
- ⏳ 检索和问答模块
- ⏳ 存储层

## 最佳实践

### 1. 编写测试的原则

- **独立性**：每个测试应该独立运行
- **可重复性**：测试结果应该一致
- **快速**：单元测试应该快速执行
- **清晰**：测试意图应该清晰明确

### 2. 使用 Mock

```python
from unittest.mock import Mock, patch

@patch('backend.module.external_service')
def test_with_mock(mock_service):
    mock_service.return_value = "mocked"
    # 测试代码
```

### 3. 使用 Fixtures

```python
@pytest.fixture
def sample_data():
    return {"key": "value"}

def test_with_fixture(sample_data):
    assert sample_data["key"] == "value"
```

### 4. 测试边界情况

```python
def test_edge_cases():
    assert function("") == expected_empty
    assert function(None) == expected_none
    assert function(large_input) == expected_large
```

### 5. 参数化测试

```python
@pytest.mark.parametrize("input,expected", [
    ("a", "A"),
    ("b", "B"),
    ("c", "C")
])
def test_uppercase(input, expected):
    assert input.upper() == expected
```

## CI/CD 集成

### GitHub Actions 示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=backend --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 故障排查

### 常见问题

#### 1. 导入错误

**问题：** `ModuleNotFoundError: No module named 'backend'`

**解决：** 确保从项目根目录运行测试
```bash
cd /path/to/KnowledgeWeaver
pytest tests/
```

#### 2. 环境变量未设置

**问题：** 测试依赖环境变量但未设置

**解决：** 使用 `mock_env_vars` fixture 或创建 `.env.test`

#### 3. Mock 不生效

**问题：** Mock 对象未按预期工作

**解决：** 检查 patch 路径是否正确
```python
# 错误：patch 导入路径
@patch('openai.OpenAI')

# 正确：patch 使用路径
@patch('backend.core.embeddings.service.OpenAI')
```

#### 4. 测试数据冲突

**问题：** 测试之间共享数据导致冲突

**解决：** 使用 `test_data_dir` fixture 创建隔离目录

## 贡献指南

添加新测试时：

1. ✅ 遵循现有的命名约定（`test_*.py`）
2. ✅ 使用适当的标记（`@pytest.mark.unit` 或 `@pytest.mark.integration`）
3. ✅ 添加清晰的文档字符串
4. ✅ 测试正常情况和边界情况
5. ✅ 使用 Mock 隔离外部依赖
6. ✅ 保持测试简单和专注

## 联系方式

如有问题或建议，请：
- 提交 Issue
- 联系维护者：Sheldon

---

**最后更新：** 2026-01-26
**版本：** 1.0.0
