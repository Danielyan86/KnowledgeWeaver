"""
Entity Filter
实体过滤模块 - 提升知识图谱质量
"""

from typing import Dict, List, Set
from ..core.language_utils import detect_language, STOP_WORDS_EN


class EntityFilter:
    """实体过滤器"""

    def __init__(self):
        # 停用实体（太通用或无意义）- 中文
        self.stop_entities = {
            # 单字通用词
            "人", "事", "物", "时", "地", "年", "月", "日",
            "个", "种", "类", "次", "度", "量", "值", "率",

            # 常见修饰词（不应单独成为实体）
            "主动", "被动", "积极", "消极", "重要", "次要",
            "大", "小", "多", "少", "高", "低", "快", "慢",
            "好", "坏", "新", "旧", "长", "短", "期限",

            # 代词
            "我", "你", "他", "她", "它", "我们", "你们", "他们",
            "这", "那", "这个", "那个", "这些", "那些",

            # 时间通用词
            "现在", "过去", "未来", "当前", "之前", "之后",
            "今天", "明天", "昨天"
        }

        # 停用实体 - 英文
        self.stop_entities_en = STOP_WORDS_EN

        # 低质量实体模式
        self.bad_patterns = [
            lambda x: len(x) == 1,  # 单字实体（通常太模糊）
            lambda x: x.isdigit(),  # 纯数字
            lambda x: any(c in x for c in "!@#$%^&*()+=[]{}|\\:;\"'<>?/"),  # 特殊字符
            lambda x: len(x) > 50,  # 过长的实体名（可能是句子）
        ]

    def should_filter(self, entity_name: str) -> bool:
        """
        判断实体是否应该被过滤（支持中英文）

        Args:
            entity_name: 实体名称

        Returns:
            True 表示应该过滤（删除），False 表示保留
        """
        # 空实体
        if not entity_name or not entity_name.strip():
            return True

        entity_name = entity_name.strip()

        # 检测语言并应用对应的停用词表
        lang = detect_language(entity_name)

        if lang == "zh":
            # 中文停用词
            if entity_name in self.stop_entities:
                return True
        else:
            # 英文停用词（小写匹配）
            if entity_name.lower() in self.stop_entities_en:
                return True

        # 检查模式
        for pattern in self.bad_patterns:
            if pattern(entity_name):
                return True

        return False

    def filter_entities(self, entities: List[Dict]) -> List[Dict]:
        """
        过滤实体列表

        Args:
            entities: 实体列表 [{"name": "xxx", "type": "xxx"}, ...]

        Returns:
            过滤后的实体列表
        """
        filtered = []
        removed = []

        for entity in entities:
            name = entity.get("name", "")
            if self.should_filter(name):
                removed.append(name)
            else:
                filtered.append(entity)

        if removed:
            print(f"过滤掉 {len(removed)} 个低质量实体: {removed[:10]}")

        return filtered

    def filter_relations(self, relations: List[Dict], valid_entities: Set[str]) -> List[Dict]:
        """
        过滤关系列表（移除引用了被过滤实体的关系）

        Args:
            relations: 关系列表
            valid_entities: 有效实体名称集合

        Returns:
            过滤后的关系列表
        """
        filtered = []
        removed_count = 0

        for relation in relations:
            source = relation.get("source", "")
            target = relation.get("target", "")

            if source in valid_entities and target in valid_entities:
                filtered.append(relation)
            else:
                removed_count += 1

        if removed_count > 0:
            print(f"过滤掉 {removed_count} 条无效关系")

        return filtered

    def normalize_relation(self, relation: str) -> str:
        """
        规范化关系类型（替换通用关系为空，后续可以推断）

        Args:
            relation: 关系名称

        Returns:
            规范化后的关系名称
        """
        # 通用关系词映射（替换为空，让后续逻辑处理）
        generic_relations = {
            "relates", "related_to", "关联", "相关",
            "涉及", "关于", "有关", "连接"
        }

        relation_lower = relation.lower().strip()

        if relation_lower in generic_relations:
            return "RELATES"  # 标记为通用关系

        return relation

    def filter_graph(self, graph: Dict) -> Dict:
        """
        过滤整个图谱

        Args:
            graph: 图谱数据 {"entities": [...], "relations": [...]}

        Returns:
            过滤后的图谱
        """
        # 过滤实体
        filtered_entities = self.filter_entities(graph.get("entities", []))

        # 构建有效实体集合
        valid_entities = {e.get("name") for e in filtered_entities}

        # 过滤关系
        filtered_relations = self.filter_relations(
            graph.get("relations", []),
            valid_entities
        )

        # 规范化关系
        for rel in filtered_relations:
            rel["relation"] = self.normalize_relation(rel.get("relation", ""))

        return {
            "entities": filtered_entities,
            "relations": filtered_relations
        }


# 单例
_filter = None

def get_entity_filter() -> EntityFilter:
    """获取实体过滤器（单例）"""
    global _filter
    if _filter is None:
        _filter = EntityFilter()
    return _filter
