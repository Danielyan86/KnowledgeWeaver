"""
Test Configuration Module
测试配置模块
"""

import pytest
from backend.core.config import (
    validate_entity,
    validate_relation,
    NODE_TYPES,
    STANDARD_RELATIONS,
    get_entity_extraction_prompt,
    get_relation_extraction_prompt
)


@pytest.mark.unit
class TestConfigValidation:
    """测试配置验证函数"""

    def test_validate_entity_success(self):
        """测试有效实体验证"""
        valid_entities = [
            {"name": "李笑来", "type": "Person"},
            {"name": "定投", "type": "Strategy"},
            {"name": "普通人", "type": "Group"},
            {"name": "标普500", "type": "Concept"}
        ]

        for entity in valid_entities:
            assert validate_entity(entity) is True

    def test_validate_entity_missing_fields(self):
        """测试缺少字段的实体"""
        invalid_entities = [
            {"name": "李笑来"},  # 缺少 type
            {"type": "Person"},  # 缺少 name
            {},  # 空字典
        ]

        for entity in invalid_entities:
            assert validate_entity(entity) is False

    def test_validate_entity_name_too_long(self):
        """测试名称过长的实体"""
        entity = {"name": "这是一个非常非常长的实体名称超过了十个字", "type": "Person"}
        assert validate_entity(entity) is False

    def test_validate_entity_invalid_type(self):
        """测试无效类型的实体"""
        entity = {"name": "李笑来", "type": "InvalidType"}
        assert validate_entity(entity) is False

    def test_validate_relation_success(self):
        """测试有效关系验证"""
        valid_relations = [
            {"source": "李笑来", "target": "书", "relation": "著作"},
            {"source": "定投", "target": "普通人", "relation": "适用于"},
            {"source": "长期主义", "target": "投资", "relation": "属于"}
        ]

        for relation in valid_relations:
            assert validate_relation(relation) is True

    def test_validate_relation_missing_fields(self):
        """测试缺少字段的关系"""
        invalid_relations = [
            {"source": "李笑来", "target": "书"},  # 缺少 relation
            {"source": "李笑来", "relation": "著作"},  # 缺少 target
            {"target": "书", "relation": "著作"},  # 缺少 source
            {},  # 空字典
        ]

        for relation in invalid_relations:
            assert validate_relation(relation) is False

    def test_validate_relation_invalid_relation_word(self):
        """测试无效的关系词"""
        relation = {"source": "A", "target": "B", "relation": "some_random_relation"}
        # 应该返回 False 因为关系词不在标准词表中
        assert validate_relation(relation) is False

    def test_node_types_defined(self):
        """测试节点类型已定义"""
        assert 'Person' in NODE_TYPES
        assert 'Book' in NODE_TYPES
        assert 'Concept' in NODE_TYPES
        assert 'Strategy' in NODE_TYPES
        assert len(NODE_TYPES) >= 7

    def test_standard_relations_defined(self):
        """测试标准关系词表已定义"""
        assert '著作' in STANDARD_RELATIONS
        assert '主张' in STANDARD_RELATIONS
        assert '适用于' in STANDARD_RELATIONS
        assert '属于' in STANDARD_RELATIONS
        assert len(STANDARD_RELATIONS) >= 10


@pytest.mark.unit
class TestPromptGeneration:
    """测试提示词生成函数"""

    def test_get_entity_extraction_prompt(self):
        """测试实体提取提示词生成"""
        text = "李笑来在《让时间陪你慢慢变富》中主张定投策略。"
        prompt = get_entity_extraction_prompt(text)

        assert text in prompt
        assert "实体提取" in prompt
        assert "节点名必须是短名词" in prompt
        assert "JSON" in prompt

    def test_get_relation_extraction_prompt(self):
        """测试关系提取提示词生成"""
        text = "李笑来在《让时间陪你慢慢变富》中主张定投策略。"
        entities = [
            {"name": "李笑来", "type": "Person"},
            {"name": "让时间陪你慢慢变富", "type": "Book"},
            {"name": "定投", "type": "Strategy"}
        ]

        prompt = get_relation_extraction_prompt(text, entities)

        assert text in prompt
        assert "关系提取" in prompt
        assert "李笑来" in prompt
        assert "让时间陪你慢慢变富" in prompt
        assert "定投" in prompt
        assert "JSON" in prompt

    def test_prompt_contains_examples(self):
        """测试提示词包含示例"""
        text = "测试文本"
        prompt = get_entity_extraction_prompt(text)

        assert "示例" in prompt or "输出格式" in prompt
