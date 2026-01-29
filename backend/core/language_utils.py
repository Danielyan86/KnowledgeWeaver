"""
Language Detection and Constants
语言检测和常量定义

提供语言检测功能和中英文验证规则。
"""

from typing import Set


def detect_language(text: str) -> str:
    """
    检测文本语言

    如果文本中 CJK 字符（中日韩统一表意文字）占比 > 50%，判定为中文，否则为英文。

    Args:
        text: 待检测文本

    Returns:
        "zh" 表示中文，"en" 表示英文
    """
    if not text or not text.strip():
        return "en"

    text = text.strip()

    # 统计 CJK 字符数量
    cjk_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')

    # 如果 CJK 字符占比 > 50%，判定为中文
    return "zh" if (cjk_count / len(text)) > 0.5 else "en"


# 名称长度限制
MAX_NAME_LENGTH_ZH = 10  # 中文最大字符数
MAX_NAME_LENGTH_EN = 30  # 英文最大字符数
MAX_NAME_WORDS_EN = 5    # 英文最大单词数


# 英文停用词（约50个常见停用词）
STOP_WORDS_EN: Set[str] = {
    # 冠词
    "a", "an", "the",

    # 代词
    "i", "you", "he", "she", "it", "we", "they",
    "me", "him", "her", "us", "them",
    "my", "your", "his", "her", "its", "our", "their",
    "mine", "yours", "hers", "ours", "theirs",
    "this", "that", "these", "those",

    # be 动词
    "be", "is", "am", "are", "was", "were", "been", "being",

    # 助动词
    "do", "does", "did", "have", "has", "had",
    "will", "would", "shall", "should", "can", "could", "may", "might", "must",

    # 介词
    "in", "on", "at", "by", "for", "with", "about", "to", "from", "of",

    # 连词
    "and", "or", "but", "if", "because", "as", "while", "when",

    # 其他
    "not", "no", "yes", "so", "very", "just", "now", "then", "here", "there"
}


# 英文标准关系词（约30个）
STANDARD_RELATIONS_EN: Set[str] = {
    # Creation
    "wrote", "authored", "created", "published", "composed",

    # Advocacy/Opinion
    "recommends", "advocates", "suggests", "proposes", "argues", "believes",

    # Hierarchy
    "belongs_to", "contains", "includes", "comprises", "part_of",

    # Application
    "applies_to", "suitable_for", "targets", "intended_for",

    # Causation
    "influences", "causes", "results_in", "leads_to", "affects",

    # Dependency
    "depends_on", "based_on", "requires", "relies_on",

    # Comparison
    "differs_from", "contrasts_with", "similar_to",

    # Characteristics
    "has_feature", "characterized_by", "properties",

    # Counter-example
    "counter_example", "not_recommended"
}


def is_english_relation(relation: str) -> bool:
    """
    检查关系词是否为英文标准关系词

    支持模糊匹配（子串匹配）

    Args:
        relation: 关系词

    Returns:
        是否为英文标准关系词
    """
    relation_lower = relation.lower().strip()

    # 直接匹配
    if relation_lower in STANDARD_RELATIONS_EN:
        return True

    # 模糊匹配（子串）
    for standard_rel in STANDARD_RELATIONS_EN:
        if standard_rel in relation_lower or relation_lower in standard_rel:
            return True

    return False


def normalize_english_relation(relation: str) -> str:
    """
    规范化英文关系词

    将关系词映射到标准关系词表中的最佳匹配

    Args:
        relation: 原始关系词

    Returns:
        规范化后的关系词，如果没有匹配则返回 "relates"
    """
    relation_lower = relation.lower().strip()

    # 直接匹配
    if relation_lower in STANDARD_RELATIONS_EN:
        return relation_lower

    # 模糊匹配（子串）
    for standard_rel in STANDARD_RELATIONS_EN:
        if standard_rel in relation_lower or relation_lower in standard_rel:
            return standard_rel

    # 默认返回通用关系
    return "relates"
