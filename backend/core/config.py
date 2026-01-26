"""
LightRAG Configuration and Prompt Templates
LightRAG 配置和提示词模板

改进的提示词确保生成规范的知识图谱数据：
- 节点名 ≤ 10 字
- 节点类型明确（Person/Book/Concept/Strategy 等）
- 关系词标准化（著作、主张、属于等）
"""

# 实体提取提示词模板
ENTITY_EXTRACTION_PROMPT = """你是一个知识图谱实体提取专家。请从以下文本中提取实体。

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

# 关系提取提示词模板
RELATION_EXTRACTION_PROMPT = """你是一个知识图谱关系提取专家。请从以下文本中提取实体之间的关系。

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

3. **提取原则**：
   - 关系必须是动词或动词短语
   - 关系要明确、具体，避免使用"相关"、"提到"等模糊词
   - 确保源实体和目标实体都已提取

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

# Few-shot 示例（用于增强提示）
FEW_SHOT_EXAMPLES = [
    {
        "input": "李笑来在《让时间陪你慢慢变富》中主张定投策略，认为定投适用于普通人，推荐标普500指数基金。",
        "output": {
            "entities": [
                {"name": "李笑来", "type": "Person"},
                {"name": "让时间陪你慢慢变富", "type": "Book"},
                {"name": "定投", "type": "Strategy"},
                {"name": "普通人", "type": "Group"},
                {"name": "标普500指数基金", "type": "Concept"}
            ],
            "relations": [
                {"source": "李笑来", "target": "让时间陪你慢慢变富", "relation": "著作"},
                {"source": "让时间陪你慢慢变富", "target": "定投", "relation": "主张"},
                {"source": "定投", "target": "普通人", "relation": "适用于"},
                {"source": "定投", "target": "标普500指数基金", "relation": "推荐"}
            ]
        }
    },
    {
        "input": "长期主义是投资的核心概念，强调时间复利的重要性。",
        "output": {
            "entities": [
                {"name": "长期主义", "type": "Concept"},
                {"name": "投资", "type": "Strategy"},
                {"name": "时间复利", "type": "Concept"}
            ],
            "relations": [
                {"source": "长期主义", "target": "投资", "relation": "属于"},
                {"source": "长期主义", "target": "时间复利", "relation": "强调"}
            ]
        }
    }
]

# 标准关系词表（用于验证和映射）
STANDARD_RELATIONS = {
    # 创作关系
    '著作', '编写', '撰写', '创作', '出版',
    # 主张/观点关系
    '主张', '强调', '提倡', '倡导', '认为',
    # 包含/属于关系
    '属于', '包含', '涵盖', '包括', '组成',
    # 适用关系
    '适用于', '适合', '针对', '面向',
    # 影响关系
    '影响', '导致', '产生', '带来',
    # 依赖关系
    '依赖', '基于', '建立在', '需要',
    # 对比关系
    '对比', '相比', '区别', '不同',
    # 推荐关系
    '推荐', '建议', '推荐标的', '推荐工具',
    # 特征关系
    '特点', '特征', '关键特征', '属性',
    # 反例关系
    '反例', '反面', '不推荐'
}

# 节点类型定义
NODE_TYPES = {
    'Person': '人物：作者、投资者、创始人等',
    'Book': '书籍：书名、著作、作品',
    'Concept': '概念：理念、理论、概念',
    'Strategy': '策略：投资策略、方法、方案',
    'Metric': '指标：数据、数值、统计指标',
    'Group': '群体：人群、用户群体',
    'Entity': '实体：其他实体'
}


def get_entity_extraction_prompt(text: str) -> str:
    """
    获取实体提取提示词
    
    Args:
        text: 待提取的文本
        
    Returns:
        完整的提示词字符串
    """
    return ENTITY_EXTRACTION_PROMPT.format(text=text)


def get_relation_extraction_prompt(text: str, entities: list) -> str:
    """
    获取关系提取提示词
    
    Args:
        text: 待提取的文本
        entities: 已提取的实体列表
        
    Returns:
        完整的提示词字符串
    """
    entities_str = ', '.join([f"{e['name']}({e['type']})" for e in entities])
    return RELATION_EXTRACTION_PROMPT.format(text=text, entities=entities_str)


def validate_entity(entity: dict) -> bool:
    """
    验证实体是否符合规范
    
    Args:
        entity: 实体字典，包含 name 和 type
        
    Returns:
        是否符合规范
    """
    if not entity.get('name') or not entity.get('type'):
        return False
    
    name = entity['name']
    entity_type = entity['type']
    
    # 检查名称长度
    if len(name) > 10:
        return False
    
    # 检查类型是否有效
    if entity_type not in NODE_TYPES:
        return False
    
    return True


def validate_relation(relation: dict) -> bool:
    """
    验证关系是否符合规范
    
    Args:
        relation: 关系字典，包含 source, target, relation
        
    Returns:
        是否符合规范
    """
    if not all(key in relation for key in ['source', 'target', 'relation']):
        return False
    
    relation_word = relation['relation']
    
    # 检查关系词是否在标准词表中
    if relation_word not in STANDARD_RELATIONS:
        # 允许部分匹配（如"推荐标的"匹配"推荐"）
        if not any(rel in relation_word for rel in STANDARD_RELATIONS):
            return False
    
    return True
