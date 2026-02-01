"""
Bilingual Configuration - 双语配置
支持中英文的实体和关系提取提示词
"""

from .language_utils import detect_language


# ========== 中文提示词（原版）==========

ENTITY_EXTRACTION_PROMPT_ZH = """你是一个知识图谱实体提取专家。请从以下文本中提取实体。

## 实体提取规则：
1. **节点名必须是短名词（≤10字），不能是句子**
   - ✅ 好：李笑来、定投、标普500指数基金
   - ❌ 差：李笑来认为普通人也能变富、投资者每月定投1000美元

2. **节点类型必须明确**，从以下类型中选择：
   - Person（人物）：作者、投资者、创始人等
   - Book（书籍）：书名、著作、作品
   - Concept（概念）：理念、理论、概念
   - Strategy（策略）：投资策略、方法、方案
   - Metric（指标）：数据、数值、统计指标
   - Group（群体）：人群、用户群体
   - Entity（实体）：其他实体

3. **提取原则**：
   - 只提取名词性实体，不提取句子或观点
   - 实体名要简洁，去除修饰词
   - 如果实体名超过10字，提取核心词

## 输出格式（JSON）：
{{
  "entities": [
    {{"name": "实体名", "type": "Person|Book|Concept|Strategy|Metric|Group|Entity"}}
  ]
}}

## 示例：
输入文本："李笑来在《让时间陪你慢慢变富》中主张定投策略，认为定投适用于普通人。"
输出：
{{
  "entities": [
    {{"name": "李笑来", "type": "Person"}},
    {{"name": "让时间陪你慢慢变富", "type": "Book"}},
    {{"name": "定投", "type": "Strategy"}},
    {{"name": "普通人", "type": "Group"}}
  ]
}}

## 待提取文本：
{text}

请提取实体："""


# ========== 英文提示词（新增）==========

ENTITY_EXTRACTION_PROMPT_EN = """You are an expert in knowledge graph entity extraction. Please extract entities from the following text.

## Entity Extraction Rules:
1. **Entity names must be short nouns (≤5 words), not sentences**
   - ✅ Good: Warren Buffett, Dollar-Cost Averaging, S&P 500 Index Fund
   - ❌ Bad: Warren Buffett believes ordinary people can become wealthy, Investors invest $1000 monthly

2. **Entity types must be explicit**, choose from:
   - Person: Authors, investors, founders, etc.
   - Book: Book titles, works, publications
   - Concept: Ideas, theories, concepts
   - Strategy: Investment strategies, methods, approaches
   - Metric: Data, values, statistics
   - Group: Demographics, user groups
   - Entity: Other entities

3. **Extraction Principles**:
   - Only extract noun entities, not sentences or opinions
   - Entity names should be concise, remove modifiers
   - If entity name exceeds 5 words, extract core terms

## Output Format (JSON):
{{
  "entities": [
    {{"name": "entity_name", "type": "Person|Book|Concept|Strategy|Metric|Group|Entity"}}
  ]
}}

## Example:
Input text: "Warren Buffett advocates the Dollar-Cost Averaging strategy in his book 'The Intelligent Investor', believing it is suitable for ordinary people."
Output:
{{
  "entities": [
    {{"name": "Warren Buffett", "type": "Person"}},
    {{"name": "The Intelligent Investor", "type": "Book"}},
    {{"name": "Dollar-Cost Averaging", "type": "Strategy"}},
    {{"name": "ordinary people", "type": "Group"}}
  ]
}}

## Text to Extract:
{text}

Please extract entities:"""


# ========== 关系提取提示词 ==========

RELATION_EXTRACTION_PROMPT_ZH = """你是一个知识图谱关系提取专家。请从以下文本中提取实体之间的关系。

## 关系提取规则：
1. **必须使用标准关系词**，从以下关系词中选择：
   - 创作类：著作、编写、撰写、创作、出版
   - 观点类：主张、强调、提倡、倡导、认为
   - 层级类：属于、包含、涵盖、包括
   - 应用类：适用于、适合、针对、面向
   - 因果类：影响、导致、产生、带来
   - 依赖类：依赖、基于、建立在、需要
   - 推荐类：推荐、建议、推荐标的、推荐工具
   - 属性类：特点、特征、关键特征、属性
   - 对比类：对比、相比、区别
   - 反例类：反例、反面、不推荐

2. **关系要能形成可查询的问题**：
   - ✅ 好：李笑来 著作 → 《让时间陪你慢慢变富》（可问：李笑来著作了什么？）
   - ✅ 好：定投 适用于 → 普通人（可问：定投适用于谁？）
   - ❌ 差：李笑来 相关 → 《让时间陪你慢慢变富》（"相关"太模糊，无法提问）

## 输出格式（JSON）：
{{
  "relations": [
    {{"source": "源实体名", "target": "目标实体名", "relation": "关系词"}}
  ]
}}

## 示例：
输入文本："李笑来在《让时间陪你慢慢变富》中主张定投策略，认为定投适用于普通人。"
输出：
{{
  "relations": [
    {{"source": "李笑来", "target": "让时间陪你慢慢变富", "relation": "著作"}},
    {{"source": "让时间陪你慢慢变富", "target": "定投", "relation": "主张"}},
    {{"source": "定投", "target": "普通人", "relation": "适用于"}}
  ]
}}

## 待提取文本：
{text}

## 已提取的实体：
{entities}

请提取关系："""


RELATION_EXTRACTION_PROMPT_EN = """You are an expert in knowledge graph relation extraction. Please extract relations between entities from the following text.

## Relation Extraction Rules:
1. **Must use standard relation types**, choose from:
   - Creation: wrote, authored, created, published, composed
   - Advocacy: recommends, advocates, suggests, proposes, argues
   - Hierarchy: belongs_to, contains, includes, part_of
   - Application: applies_to, suitable_for, targets, intended_for
   - Causation: influences, causes, results_in, leads_to, affects
   - Dependency: depends_on, based_on, requires, relies_on
   - Comparison: differs_from, contrasts_with, similar_to
   - Characteristics: has_feature, characterized_by
   - Counter: counter_example, not_recommended

2. **Relations should form queryable questions**:
   - ✅ Good: Warren Buffett authored → The Intelligent Investor (Query: What did Warren Buffett author?)
   - ✅ Good: Dollar-Cost Averaging suitable_for → ordinary people (Query: Who is DCA suitable for?)
   - ❌ Bad: Warren Buffett relates → The Intelligent Investor ("relates" is too vague)

## Output Format (JSON):
{{
  "relations": [
    {{"source": "source_entity", "target": "target_entity", "relation": "relation_type"}}
  ]
}}

## Example:
Input text: "Warren Buffett advocates the Dollar-Cost Averaging strategy in his book 'The Intelligent Investor', believing it is suitable for ordinary people."
Output:
{{
  "relations": [
    {{"source": "Warren Buffett", "target": "The Intelligent Investor", "relation": "authored"}},
    {{"source": "The Intelligent Investor", "target": "Dollar-Cost Averaging", "relation": "advocates"}},
    {{"source": "Dollar-Cost Averaging", "target": "ordinary people", "relation": "suitable_for"}}
  ]
}}

## Text to Extract:
{text}

## Extracted Entities:
{entities}

Please extract relations:"""


# ========== 动态选择提示词 ==========

def get_entity_extraction_prompt(text: str) -> str:
    """
    根据文本语言动态选择提示词模板

    Args:
        text: 待提取的文本

    Returns:
        完整的提示词字符串
    """
    lang = detect_language(text)

    if lang == "zh":
        return ENTITY_EXTRACTION_PROMPT_ZH.format(text=text)
    else:
        return ENTITY_EXTRACTION_PROMPT_EN.format(text=text)


def get_relation_extraction_prompt(text: str, entities: list) -> str:
    """
    根据文本语言动态选择提示词模板

    Args:
        text: 待提取的文本
        entities: 已提取的实体列表

    Returns:
        完整的提示词字符串
    """
    lang = detect_language(text)
    entities_str = ', '.join([f"{e['name']}({e['type']})" for e in entities])

    if lang == "zh":
        return RELATION_EXTRACTION_PROMPT_ZH.format(text=text, entities=entities_str)
    else:
        return RELATION_EXTRACTION_PROMPT_EN.format(text=text, entities=entities_str)
