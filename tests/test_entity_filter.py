"""
Test Entity Filter
测试实体过滤器
"""

import pytest
from backend.extraction.entity_filter import EntityFilter, get_entity_filter


@pytest.mark.unit
class TestEntityFilter:
    """测试实体过滤器"""

    @pytest.fixture
    def filter(self):
        """创建过滤器实例"""
        return EntityFilter()

    def test_should_filter_empty(self, filter):
        """测试过滤空实体"""
        assert filter.should_filter("") is True
        assert filter.should_filter("  ") is True
        assert filter.should_filter(None) is True

    def test_should_filter_stop_words(self, filter):
        """测试过滤停用词"""
        stop_entities = ["人", "事", "物", "我", "你", "他", "这", "那"]
        for entity in stop_entities:
            assert filter.should_filter(entity) is True

    def test_should_filter_single_char(self, filter):
        """测试过滤单字实体"""
        assert filter.should_filter("年") is True
        assert filter.should_filter("书") is True

    def test_should_filter_pure_numbers(self, filter):
        """测试过滤纯数字"""
        assert filter.should_filter("123") is True
        assert filter.should_filter("456789") is True

    def test_should_filter_special_chars(self, filter):
        """测试过滤特殊字符"""
        assert filter.should_filter("测试@#$") is True
        assert filter.should_filter("<script>") is True

    def test_should_filter_too_long(self, filter):
        """测试过滤过长实体"""
        long_entity = "这是一个非常非常长的实体名称超过了五十个字符的限制应该被过滤掉的测试用例数据"
        assert filter.should_filter(long_entity) is True

    def test_should_not_filter_valid(self, filter):
        """测试不过滤有效实体"""
        valid_entities = ["李笑来", "定投策略", "标普500", "让时间陪你慢慢变富"]
        for entity in valid_entities:
            assert filter.should_filter(entity) is False

    def test_filter_entities(self, filter, sample_entities):
        """测试过滤实体列表"""
        # 添加一些无效实体
        entities_with_invalid = sample_entities + [
            {"name": "人", "type": "Entity"},
            {"name": "123", "type": "Metric"},
            {"name": "", "type": "Entity"}
        ]

        filtered = filter.filter_entities(entities_with_invalid)

        # 应该过滤掉3个无效实体
        assert len(filtered) == len(sample_entities)

        # 检查过滤后的实体名称
        filtered_names = {e["name"] for e in filtered}
        for entity in sample_entities:
            assert entity["name"] in filtered_names

    def test_filter_relations(self, filter):
        """测试过滤关系"""
        relations = [
            {"source": "李笑来", "target": "书", "relation": "著作"},
            {"source": "无效实体", "target": "书", "relation": "相关"},
            {"source": "李笑来", "target": "另一个无效", "relation": "主张"}
        ]

        valid_entities = {"李笑来", "书"}
        filtered = filter.filter_relations(relations, valid_entities)

        # 只保留第一条关系
        assert len(filtered) == 1
        assert filtered[0]["source"] == "李笑来"
        assert filtered[0]["target"] == "书"

    def test_normalize_relation(self, filter):
        """测试关系规范化"""
        assert filter.normalize_relation("相关") == "RELATES"
        assert filter.normalize_relation("关联") == "RELATES"
        assert filter.normalize_relation("涉及") == "RELATES"
        assert filter.normalize_relation("著作") == "著作"

    def test_filter_graph(self, filter):
        """测试过滤整个图谱"""
        graph = {
            "entities": [
                {"name": "李笑来", "type": "Person"},
                {"name": "定投", "type": "Strategy"},
                {"name": "人", "type": "Entity"},  # 无效
                {"name": "123", "type": "Metric"}  # 无效
            ],
            "relations": [
                {"source": "李笑来", "target": "定投", "relation": "主张"},
                {"source": "李笑来", "target": "人", "relation": "相关"},  # 无效目标
                {"source": "定投", "target": "123", "relation": "包含"}  # 无效目标
            ]
        }

        filtered = filter.filter_graph(graph)

        # 应该只保留2个有效实体
        assert len(filtered["entities"]) == 2

        # 应该只保留1条有效关系
        assert len(filtered["relations"]) == 1
        assert filtered["relations"][0]["source"] == "李笑来"
        assert filtered["relations"][0]["target"] == "定投"

    def test_get_entity_filter_singleton(self):
        """测试单例模式"""
        filter1 = get_entity_filter()
        filter2 = get_entity_filter()
        assert filter1 is filter2
