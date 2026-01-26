# KnowledgeWeaver 测试套件

完整的单元测试和集成测试套件。

## 测试结构

```
tests/
├── conftest.py                # pytest 配置和共享 fixtures
├── pytest.ini                 # pytest 配置文件
├── test_config.py            # 配置模块测试
├── test_normalizer.py        # 图谱规范化测试
├── test_entity_filter.py     # 实体过滤测试
├── test_embeddings.py        # 嵌入服务测试
├── test_kg_manager.py        # KG 管理器测试
├── test_progress_tracker.py  # 进度追踪测试
├── test_api.py               # API 端点测试
└── README.md                 # 本文件
```

## 运行测试

### 安装测试依赖

```bash
pip install -r requirements.txt
```

### 运行全部测试

```bash
# 从项目根目录运行
pytest

# 或者指定测试目录
pytest tests/
```

### 运行特定测试文件

```bash
pytest tests/test_config.py
pytest tests/test_normalizer.py
```

### 运行特定测试类或函数

```bash
# 运行特定测试类
pytest tests/test_config.py::TestConfigValidation

# 运行特定测试函数
pytest tests/test_config.py::TestConfigValidation::test_validate_entity_success
```

### 按标记运行测试

```bash
# 只运行单元测试
pytest -m unit

# 只运行集成测试
pytest -m integration

# 排除慢速测试
pytest -m "not slow"
```

### 生成覆盖率报告

```bash
# 运行测试并生成覆盖率报告
pytest --cov=backend --cov-report=html

# 查看报告
open htmlcov/index.html
```

### 详细输出

```bash
# 显示详细输出
pytest -v

# 显示打印语句
pytest -s

# 显示局部变量
pytest -l
```

## 测试覆盖范围

### 核心模块

- ✅ `config.py` - 配置和验证函数
- ✅ `embeddings/service.py` - 嵌入服务
- ✅ `storage/vector.py` - 向量存储（部分）
- ⏳ `storage/neo4j.py` - Neo4j 存储（待添加）

### 提取模块

- ✅ `normalizer.py` - 图谱规范化
- ✅ `entity_filter.py` - 实体过滤
- ⏳ `extractor.py` - 知识提取（待添加）
- ⏳ `async_extractor.py` - 异步提取（待添加）

### 检索模块

- ⏳ `hybrid_retriever.py` - 混合检索（待添加）
- ⏳ `qa_engine.py` - 问答引擎（待添加）

### 管理模块

- ✅ `kg_manager.py` - 知识图谱管理器
- ✅ `progress_tracker.py` - 进度追踪

### API 端点

- ✅ 健康检查
- ✅ 图谱查询端点
- ✅ 文档管理端点
- ✅ 统计端点
- ✅ 问答端点
- ✅ 上传端点

## Fixtures

### 数据 Fixtures

- `sample_entities` - 示例实体列表
- `sample_relations` - 示例关系列表
- `sample_graph` - 示例知识图谱
- `sample_chunks` - 示例文本块

### 环境 Fixtures

- `mock_env_vars` - 模拟环境变量
- `test_data_dir` - 临时测试数据目录
- `sample_text_file` - 示例文本文件

### 服务 Fixtures

- `api_client` - FastAPI 测试客户端
- `mock_neo4j_storage` - 模拟 Neo4j 存储
- `mock_openai_client` - 模拟 OpenAI 客户端

## 测试最佳实践

### 1. 使用标记区分测试类型

```python
@pytest.mark.unit
def test_unit_function():
    pass

@pytest.mark.integration
def test_integration_function():
    pass

@pytest.mark.slow
def test_slow_function():
    pass
```

### 2. 使用 Mock 隔离外部依赖

```python
from unittest.mock import Mock, patch

@patch('backend.module.external_service')
def test_with_mock(mock_service):
    mock_service.return_value = "mocked result"
    # 测试代码
```

### 3. 使用 Fixtures 共享测试数据

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
    # 测试空输入
    assert function("") == expected_empty

    # 测试 None 输入
    assert function(None) == expected_none

    # 测试极端值
    assert function(sys.maxsize) == expected_max
```

## 持续集成

可以在 CI/CD 管道中运行测试：

```yaml
# .github/workflows/test.yml
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
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest --cov=backend --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 调试测试

### 使用 pdb 调试

```bash
# 在失败时进入 pdb
pytest --pdb

# 在开始时进入 pdb
pytest --trace
```

### 只运行失败的测试

```bash
# 首次运行
pytest

# 只重新运行失败的测试
pytest --lf
```

### 显示最慢的测试

```bash
pytest --durations=10
```

## 贡献指南

添加新测试时：

1. 遵循现有的命名约定
2. 使用适当的标记（@pytest.mark.unit 或 @pytest.mark.integration）
3. 添加清晰的文档字符串
4. 测试正常情况和边界情况
5. 使用 Mock 隔离外部依赖
6. 保持测试简单和专注

## 问题排查

### 导入错误

确保从项目根目录运行测试：

```bash
cd /path/to/KnowledgeWeaver
pytest tests/
```

### 环境变量未设置

使用 `mock_env_vars` fixture 或创建 `.env.test` 文件。

### 测试数据冲突

使用 `test_data_dir` fixture 创建隔离的临时目录。

## 联系方式

如有问题，请联系维护者或提交 Issue。
