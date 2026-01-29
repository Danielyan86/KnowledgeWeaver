"""
Bilingual Validation Test
测试中英文验证功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.core.language_utils import (
    detect_language,
    is_english_relation,
    normalize_english_relation,
    STOP_WORDS_EN,
    MAX_NAME_LENGTH_ZH,
    MAX_NAME_LENGTH_EN,
    MAX_NAME_WORDS_EN
)
from backend.extraction.entity_filter import EntityFilter
from backend.extraction.normalizer import KnowledgeGraphNormalizer


def test_language_detection():
    """测试语言检测"""
    print("\n=== 测试语言检测 ===")

    test_cases = [
        ("李笑来", "zh"),
        ("Warren Buffett", "en"),
        ("让时间陪你慢慢变富", "zh"),
        ("The Intelligent Investor", "en"),
        ("定投", "zh"),
        ("value investing", "en"),
        ("S&P 500", "en"),
        ("标普500指数", "zh"),
        ("", "en"),  # 空字符串默认英文
    ]

    for text, expected_lang in test_cases:
        detected = detect_language(text)
        status = "✅" if detected == expected_lang else "❌"
        print(f"{status} '{text}' -> {detected} (expected: {expected_lang})")


def test_entity_filter():
    """测试实体过滤"""
    print("\n=== 测试实体过滤 ===")

    filter = EntityFilter()

    test_cases = [
        # 中文停用词
        ("我", True),
        ("这个", True),
        ("人", True),

        # 英文停用词
        ("the", True),
        ("it", True),
        ("he", True),

        # 有效实体
        ("李笑来", False),
        ("Warren Buffett", False),
        ("定投", False),
        ("value investing", False),

        # 空字符串
        ("", True),
        ("   ", True),
    ]

    for entity_name, should_filter in test_cases:
        result = filter.should_filter(entity_name)
        status = "✅" if result == should_filter else "❌"
        action = "过滤" if result else "保留"
        print(f"{status} '{entity_name}' -> {action} (expected: {'过滤' if should_filter else '保留'})")


def test_node_name_normalization():
    """测试节点名称规范化"""
    print("\n=== 测试节点名称规范化 ===")

    normalizer = KnowledgeGraphNormalizer()

    test_cases = [
        # 中文：≤10 字符
        ("李笑来", "李笑来"),
        ("让时间陪你慢慢变富", "让时间陪你慢慢变"),  # 超过10字，截断
        ("《让时间陪你慢慢变富》", "让时间陪你慢慢变"),  # 去除书名号并截断

        # 英文：≤5 单词 或 ≤30 字符
        ("Warren Buffett", "Warren Buffett"),  # 2 words, OK
        ("The Intelligent Investor", "The Intelligent Investor"),  # 3 words, OK
        ("Complete Guide to Value Investing for Beginners", "Complete Guide to Value Investing"),  # 7 words -> 5 words
        ("A Very Long Book Title That Exceeds Thirty Characters", "A Very Long Book Title That Ex"),  # 超过30字符，截断

        # 特殊字符处理
        ("  Warren   Buffett  ", "Warren Buffett"),  # 多余空格
        ('"value investing"', "value investing"),  # 引号
    ]

    for original, expected in test_cases:
        normalized = normalizer.normalize_node_name(original)
        status = "✅" if normalized == expected else "❌"
        print(f"{status} '{original}' -> '{normalized}' (expected: '{expected}')")


def test_relation_normalization():
    """测试关系规范化"""
    print("\n=== 测试关系规范化 ===")

    normalizer = KnowledgeGraphNormalizer()

    test_cases = [
        # 中文关系
        ("著作", "著作"),
        ("主张", "主张"),
        ("适用于", "适用于"),

        # 英文关系
        ("wrote", "wrote"),
        ("recommends", "recommends"),
        ("suitable_for", "suitable_for"),
        ("applies_to", "applies_to"),

        # 模糊匹配
        ("推荐标的", "推荐"),  # 中文模糊匹配
        ("recommended", "recommends"),  # 英文模糊匹配（如果实现）

        # 未知关系
        ("unknown_relation", "relates"),  # 英文默认
        ("未知关系词汇", "未知关系词汇"),  # 中文短词保留
    ]

    for original, expected in test_cases:
        normalized = normalizer.normalize_relation(original)
        # 注意：对于中文，可能返回不同的标准化值
        print(f"'{original}' -> '{normalized}' (expected: '{expected}')")


def test_english_relation_validation():
    """测试英文关系词验证"""
    print("\n=== 测试英文关系词验证 ===")

    test_cases = [
        ("wrote", True),
        ("recommends", True),
        ("suitable_for", True),
        ("belongs_to", True),
        ("unknown", False),
        ("relates", False),  # 通用关系不在标准词表
    ]

    for relation, is_valid in test_cases:
        result = is_english_relation(relation)
        status = "✅" if result == is_valid else "❌"
        print(f"{status} '{relation}' -> {'有效' if result else '无效'} (expected: {'有效' if is_valid else '无效'})")


def test_constants():
    """测试常量配置"""
    print("\n=== 测试常量配置 ===")

    print(f"中文最大字符数: {MAX_NAME_LENGTH_ZH}")
    print(f"英文最大字符数: {MAX_NAME_LENGTH_EN}")
    print(f"英文最大单词数: {MAX_NAME_WORDS_EN}")
    print(f"英文停用词数量: {len(STOP_WORDS_EN)}")

    # 验证一些常见停用词
    common_stop_words = ["the", "a", "it", "is", "he", "she"]
    for word in common_stop_words:
        if word in STOP_WORDS_EN:
            print(f"✅ '{word}' 在停用词表中")
        else:
            print(f"❌ '{word}' 不在停用词表中")


if __name__ == "__main__":
    print("=" * 60)
    print("双语验证功能测试")
    print("=" * 60)

    test_language_detection()
    test_entity_filter()
    test_node_name_normalization()
    test_relation_normalization()
    test_english_relation_validation()
    test_constants()

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
