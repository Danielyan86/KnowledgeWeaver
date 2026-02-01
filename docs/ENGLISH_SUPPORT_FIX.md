# 英文资料图谱不显示问题 - 完整解决方案

## 问题诊断

### 根本原因

**提示词模板只有中文示例，导致 LLM 对英文文本提取效果差。**

```python
# backend/core/config.py (当前)
ENTITY_EXTRACTION_PROMPT = """你是一个知识图谱实体提取专家...
## 示例：
输入文本："李笑来在《让时间陪你慢慢变富》中主张定投策略..."  # ❌ 只有中文示例
```

### 系统已有但未使用的功能

系统已经有完整的英文支持：
- ✅ `language_utils.py` - 语言检测
- ✅ `entity_filter.py` - 英文停用词
- ✅ `STOP_WORDS_EN`, `STANDARD_RELATIONS_EN` - 英文词表

**但是**：提取时没有根据语言选择提示词！

## 诊断步骤

### 1. 检查 Neo4j 中是否有数据

```bash
# 打开 Neo4j Browser: http://localhost:7474
# 运行以下查询：

// 查看所有实体
MATCH (n:Entity) RETURN n.id, n.type LIMIT 50

// 搜索英文实体
MATCH (n:Entity)
WHERE n.id =~ '.*[a-zA-Z]+.*'
RETURN n.id, n.type, n.doc_ids
LIMIT 20

// 统计总数
MATCH (n:Entity) RETURN count(n) as total_entities
```

### 2. 检查向量数据库

```python
from backend.core.storage import get_vector_store

vector_store = get_vector_store()
results = vector_store.collection.get(limit=10)
print(f"文档数量: {len(results['ids'])}")
for text in results['documents'][:5]:
    print(text[:100])
```

### 3. 查看处理日志

```bash
# 查看最近的日志
tail -n 100 logs/server.log | grep -i "extract\|entity\|filter"
```

## 解决方案

### 方案 1：使用双语配置文件（推荐）✅

#### 步骤 1: 更新 config.py

用双语版本替换提示词获取函数：

```python
# backend/core/config.py

# 在文件末尾添加：
from .language_utils import detect_language

def get_entity_extraction_prompt(text: str) -> str:
    """根据文本语言动态选择提示词"""
    lang = detect_language(text)

    if lang == "zh":
        # 使用中文提示词（原版）
        return ENTITY_EXTRACTION_PROMPT.format(text=text)
    else:
        # 使用英文提示词
        return ENTITY_EXTRACTION_PROMPT_EN.format(text=text)


def get_relation_extraction_prompt(text: str, entities: list) -> str:
    """根据文本语言动态选择提示词"""
    lang = detect_language(text)
    entities_str = ', '.join([f"{e['name']}({e['type']})" for e in entities])

    if lang == "zh":
        return RELATION_EXTRACTION_PROMPT.format(text=text, entities=entities_str)
    else:
        return RELATION_EXTRACTION_PROMPT_EN.format(text=text, entities=entities_str)
```

#### 步骤 2: 添加英文提示词模板

在 `config.py` 中添加：

```python
# 英文实体提取提示词
ENTITY_EXTRACTION_PROMPT_EN = """You are an expert in knowledge graph entity extraction.

## Rules:
1. **Entity names must be short nouns (≤5 words)**
   - ✅ Good: Warren Buffett, Dollar-Cost Averaging
   - ❌ Bad: Warren Buffett believes people can become wealthy

2. **Entity types**: Person, Book, Concept, Strategy, Metric, Group, Entity

## Output (JSON):
{{
  "entities": [
    {{"name": "entity_name", "type": "Person|Book|..."}}
  ]
}}

## Example:
Input: "Warren Buffett advocates Dollar-Cost Averaging in 'The Intelligent Investor'."
Output:
{{
  "entities": [
    {{"name": "Warren Buffett", "type": "Person"}},
    {{"name": "The Intelligent Investor", "type": "Book"}},
    {{"name": "Dollar-Cost Averaging", "type": "Strategy"}}
  ]
}}

## Text:
{text}

Extract entities:"""

# 英文关系提取提示词
RELATION_EXTRACTION_PROMPT_EN = """You are an expert in relation extraction.

## Standard Relations:
- Creation: wrote, authored, created
- Advocacy: recommends, advocates, suggests
- Hierarchy: belongs_to, contains
- Application: applies_to, suitable_for
- Causation: influences, causes
- Dependency: depends_on, based_on

## Output (JSON):
{{
  "relations": [
    {{"source": "entity1", "target": "entity2", "relation": "relation_type"}}
  ]
}}

## Text:
{text}

## Entities:
{entities}

Extract relations:"""
```

#### 步骤 3: 更新提取器使用新函数

确认提取器使用 `get_entity_extraction_prompt()` 而不是直接使用模板：

```python
# backend/extraction/async_extractor.py 或 extractor.py
from ..core.config import get_entity_extraction_prompt, get_relation_extraction_prompt

# 使用函数获取提示词（会自动检测语言）
prompt = get_entity_extraction_prompt(chunk_text)
```

#### 步骤 4: 重启服务并重新处理文档

```bash
# 重启服务
./scripts/restart.sh

# 重新上传英文文档（系统会用新的提示词处理）
curl -X POST "http://localhost:9621/documents/upload-async" \
  -F "file=@your_english_document.txt"
```

### 方案 2：直接替换配置文件（更简单）

```bash
# 1. 备份原文件
cp backend/core/config.py backend/core/config.py.backup

# 2. 使用双语版本
cp backend/core/config_bilingual.py backend/core/config.py

# 3. 重启服务
./scripts/restart.sh
```

## 验证修复

### 1. 测试英文提取

```bash
# 上传测试文件
cat > test_english.txt << 'EOF'
Warren Buffett is a legendary investor who advocates the value investing strategy.
In his book "The Intelligent Investor", he recommends Dollar-Cost Averaging for ordinary investors.
This strategy is suitable for long-term wealth accumulation.
EOF

curl -X POST "http://localhost:9621/documents/upload-async" \
  -F "file=@test_english.txt"
```

### 2. 检查提取结果

```cypher
// 在 Neo4j Browser 中查询
MATCH (n:Entity)
WHERE n.id IN ['Warren Buffett', 'The Intelligent Investor', 'Dollar-Cost Averaging']
RETURN n

// 查看关系
MATCH (n1:Entity)-[r]->(n2:Entity)
WHERE n1.id = 'Warren Buffett'
RETURN n1.id, type(r), n2.id
```

### 3. 查看图谱

访问 http://localhost:9621，应该能看到英文实体和关系了！

## 预期效果

修复后，英文文档应该正确提取：

```json
{
  "entities": [
    {"name": "Warren Buffett", "type": "Person"},
    {"name": "The Intelligent Investor", "type": "Book"},
    {"name": "Dollar-Cost Averaging", "type": "Strategy"},
    {"name": "value investing", "type": "Strategy"},
    {"name": "ordinary investors", "type": "Group"}
  ],
  "relations": [
    {"source": "Warren Buffett", "target": "value investing", "relation": "advocates"},
    {"source": "Warren Buffett", "target": "The Intelligent Investor", "relation": "authored"},
    {"source": "The Intelligent Investor", "target": "Dollar-Cost Averaging", "relation": "recommends"},
    {"source": "Dollar-Cost Averaging", "target": "ordinary investors", "relation": "suitable_for"}
  ]
}
```

## 其他可能的问题

### 问题 1: 前端不显示英文节点

**原因**：前端 D3.js 可能对英文长名称换行处理不好。

**解决**：检查 `frontend/kg-visualization.js` 中的文本渲染逻辑。

### 问题 2: LLM 模型问题

**原因**：使用的 LLM 模型对英文支持不好（例如某些中文优化的模型）。

**解决**：切换到对英文支持更好的模型：

```bash
# .env
LLM_MODEL=gpt-4              # OpenAI
LLM_MODEL=claude-3-sonnet    # Anthropic
LLM_MODEL=deepseek-chat      # DeepSeek（中英文都好）
```

### 问题 3: 文档编码问题

**原因**：英文文档编码不是 UTF-8。

**解决**：确保文件是 UTF-8 编码：

```bash
file -I your_document.txt
# 应该显示: charset=utf-8
```

## 快速修复命令

```bash
# 一键修复（推荐执行）
cd /Users/sheldon/Github/KnowledgeWeaver

# 1. 备份
cp backend/core/config.py backend/core/config.py.backup

# 2. 使用双语版本
cp backend/core/config_bilingual.py backend/core/config.py

# 3. 重启
./scripts/restart.sh

# 4. 重新上传英文文档
# （手动操作，或使用 curl）
```

## 总结

**问题**：提示词只有中文示例，LLM 对英文提取效果差
**解决**：使用双语提示词，根据文档语言自动选择
**效果**：中英文文档都能正确提取实体和关系

---

**创建日期**: 2026-01-31
**维护者**: Sheldon
**状态**: 待修复
