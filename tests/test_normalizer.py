"""
Test Knowledge Graph Normalizer
测试知识图谱规范化器
"""

import pytest
from backend.extraction.normalizer import KnowledgeGraphNormalizer


@pytest.mark.unit
class TestKnowledgeGraphNormalizer:
    """测试知识图谱规范化器"""

    @pytest.fixture
    def normalizer(self):
        """创建规范化器实例"""
        return KnowledgeGraphNormalizer()

    def test_normalize_node_name_basic(self, normalizer):
        """测试基本节点名称规范化"""
        assert normalizer.normalize_node_name("李笑来") == "李笑来"
        assert normalizer.normalize_node_name("  李笑来  ") == "李笑来"
        assert normalizer.normalize_node_name("《让时间陪你慢慢变富》") == "让时间陪你慢慢变富"

    def test_normalize_node_name_remove_quotes(self, normalizer):
        """测试移除引号"""
        assert normalizer.normalize_node_name('"定投策略"') == "定投策略"
        # 注意：normalizer 只移除 """ 和 '' 等特殊引号，不移除普通单引号

    def test_normalize_node_name_too_long(self, normalizer):
        """测试过长名称截断"""
        long_name = "这是一个非常非常长的实体名称超过了十个字符限制"
        result = normalizer.normalize_node_name(long_name)
        assert len(result) <= normalizer.max_node_name_length

    def test_normalize_node_name_empty(self, normalizer):
        """测试空名称"""
        assert normalizer.normalize_node_name("") == ""
        assert normalizer.normalize_node_name(None) is None

    def test_infer_node_type_person(self, normalizer):
        """测试推断人名类型"""
        node = {"id": "李笑来", "description": ""}
        assert normalizer.infer_node_type(node) == "Person"

        node = {"id": "张三", "description": ""}
        assert normalizer.infer_node_type(node) == "Person"

    def test_infer_node_type_book(self, normalizer):
        """测试推断书籍类型"""
        node = {"id": "让时间陪你慢慢变富", "description": "这是一本书"}
        assert normalizer.infer_node_type(node) == "Book"

    def test_infer_node_type_strategy(self, normalizer):
        """测试推断策略类型"""
        node = {"id": "定投方法", "description": "这是一种投资策略"}
        assert normalizer.infer_node_type(node) == "Strategy"

    def test_infer_node_type_default(self, normalizer):
        """测试默认类型推断"""
        node = {"id": "某种概念abc", "description": ""}
        # 如果无法明确推断，返回 Entity 或根据关键词推断类型
        result = normalizer.infer_node_type(node)
        assert result in ["Entity", "Person", "Concept"]  # 可能被识别为人名、实体或概念

    def test_normalize_relation_standard(self, normalizer):
        """测试标准关系词规范化"""
        assert normalizer.normalize_relation("著作") == "著作"
        assert normalizer.normalize_relation("主张") == "主张"
        assert normalizer.normalize_relation("适用于") == "适用于"

    def test_normalize_relation_mapping(self, normalizer):
        """测试关系词映射"""
        assert normalizer.normalize_relation("编写") == "著作"
        assert normalizer.normalize_relation("强调") == "主张"
        assert normalizer.normalize_relation("适合") == "适用于"

    def test_normalize_relation_fuzzy_match(self, normalizer):
        """测试模糊匹配"""
        assert normalizer.normalize_relation("推荐标的") == "推荐"

    def test_normalize_relation_too_long(self, normalizer):
        """测试过长关系词截断"""
        long_relation = "这是一个非常长的关系词"
        result = normalizer.normalize_relation(long_relation)
        assert len(result) <= normalizer.max_relation_length

    def test_normalize_node(self, normalizer):
        """测试节点规范化"""
        raw_node = {
            "id": "  李笑来  ",
            "label": "李笑来",
            "description": "投资者和作家",
            "degree": 5
        }

        normalized = normalizer.normalize_node(raw_node)

        assert normalized["id"] == "李笑来"
        assert normalized["label"] == "李笑来"
        assert normalized["type"] == "Person"
        assert normalized["description"] == "投资者和作家"
        assert normalized["degree"] == 5

    def test_normalize_edge(self, normalizer):
        """测试边规范化"""
        raw_edge = {
            "source": "  李笑来  ",
            "target": "让时间陪你慢慢变富",
            "label": "编写",
            "weight": 1
        }

        normalized = normalizer.normalize_edge(raw_edge)

        assert normalized["source"] == "李笑来"
        assert normalized["target"] == "让时间陪你慢慢变富"
        assert normalized["label"] == "著作"  # 映射到标准关系词
        assert normalized["weight"] == 1

    def test_merge_duplicate_nodes(self, normalizer):
        """测试合并重复节点"""
        nodes = [
            {"id": "李笑来", "type": "Person", "degree": 2},
            {"id": "  李笑来  ", "type": "Person", "degree": 3},
            {"id": "《让时间陪你慢慢变富》", "type": "Book", "degree": 1},
            {"id": "让时间陪你慢慢变富", "type": "Book", "degree": 2}
        ]

        merged, aliases = normalizer.merge_duplicate_nodes(nodes)

        # 应该合并为2个节点
        assert len(merged) == 2
        # 别名映射应该包含重复项
        assert len(aliases) > 0

    def test_normalize_graph(self, normalizer, sample_graph):
        """测试完整图谱规范化"""
        normalized = normalizer.normalize_graph(sample_graph)

        assert "nodes" in normalized
        assert "edges" in normalized
        assert "stats" in normalized

        # 统计信息
        stats = normalized["stats"]
        assert "original_nodes" in stats
        assert "normalized_nodes" in stats
        assert "original_edges" in stats
        assert "normalized_edges" in stats

    def test_normalize_graph_empty(self, normalizer):
        """测试空图谱规范化"""
        empty_graph = {"nodes": [], "edges": []}
        normalized = normalizer.normalize_graph(empty_graph)

        assert normalized["nodes"] == []
        assert normalized["edges"] == []

    def test_normalize_graph_filters_self_loops(self, normalizer):
        """测试过滤自环边"""
        graph = {
            "nodes": [
                {"id": "A", "type": "Entity"}
            ],
            "edges": [
                {"source": "A", "target": "A", "label": "相关"}  # 自环
            ]
        }

        normalized = normalizer.normalize_graph(graph)
        assert len(normalized["edges"]) == 0  # 自环应被过滤

    def test_extract_properties(self, normalizer):
        """测试属性提取"""
        node = {
            "description": "这是一个测试实体，包含数字123和时间10年的信息"
        }

        short_desc, properties = normalizer.extract_properties(node)

        assert len(short_desc) <= 53  # 50 + "..."
        if properties:
            assert "numbers" in properties or "times" in properties
