"""
Knowledge Graph Normalizer
知识图谱规范化模块

核心功能：
1. 节点名称规范化（缩短、去重、合并）
2. 节点类型标准化
3. 关系词规范化（映射到标准关系词表）
4. 属性提取和分离
"""

import re
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict


class KnowledgeGraphNormalizer:
    """知识图谱数据规范化器"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化规范化器
        
        Args:
            config: 配置字典，包含节点类型、关系词表等
        """
        self.config = config or {}
        
        # 节点类型定义
        self.node_types = self.config.get('node_types', {
            'Person': ['人', '作者', '作家', '投资者', '创始人'],
            'Book': ['书', '书籍', '著作', '作品'],
            'Concept': ['概念', '理念', '方法', '策略', '理论'],
            'Strategy': ['策略', '方法', '投资策略', '理财方法'],
            'Metric': ['指标', '数据', '数值', '统计'],
            'Example': ['例子', '案例', '实例', '示例'],
            'Group': ['群体', '人群', '投资者', '普通人'],
            'Entity': ['实体', '对象']  # 默认类型
        })
        
        # 标准关系词表（可提问、可复用）
        self.standard_relations = self.config.get('standard_relations', {
            # 创作关系
            '著作': '著作',
            '编写': '著作',
            '撰写': '著作',
            '创作': '著作',
            '出版': '著作',
            
            # 主张/观点关系
            '主张': '主张',
            '强调': '主张',
            '提倡': '主张',
            '倡导': '主张',
            '认为': '主张',
            '观点': '主张',
            
            # 包含/属于关系
            '属于': '属于',
            '包含': '包含',
            '涵盖': '包含',
            '包括': '包含',
            '组成': '包含',
            
            # 适用关系
            '适用于': '适用于',
            '适合': '适用于',
            '针对': '适用于',
            '面向': '适用于',
            
            # 影响关系
            '影响': '影响',
            '导致': '影响',
            '产生': '影响',
            '带来': '影响',
            
            # 依赖关系
            '依赖': '依赖',
            '基于': '依赖',
            '建立在': '依赖',
            '需要': '依赖',
            
            # 对比关系
            '对比': '对比',
            '相比': '对比',
            '区别': '对比',
            '不同': '对比',
            
            # 推荐关系
            '推荐': '推荐',
            '建议': '推荐',
            '推荐标的': '推荐',
            '推荐工具': '推荐',
            
            # 特征关系
            '特点': '特点',
            '特征': '特点',
            '关键特征': '特点',
            '属性': '特点',
            
            # 反例关系
            '反例': '反例',
            '反面': '反例',
            '不推荐': '反例',
            '不熟悉': '反例',
            '不保证': '反例',

            # 因果/决定关系
            '决定': '决定',
            '取决于': '决定',
            '由...决定': '决定',

            # 解决关系
            '解决': '解决',
            '应对': '解决',
            '处理': '解决',

            # 面临关系
            '面临': '面临',
            '遭遇': '面临',
            '面对': '面临',

            # 相似关系
            '类似': '类似',
            '相似': '类似',
            '像': '类似',

            # 通过关系
            '可通过': '通过',
            '通过': '通过',
            '借助': '通过',

            # 具有关系
            '具有': '具有',
            '拥有': '具有',
            '有': '具有',

            # 计算关系
            '计算': '计算',
            '得出': '计算'
        })
        
        # 节点名称最大长度
        self.max_node_name_length = self.config.get('max_node_name_length', 10)
        
        # 关系名称最大长度
        self.max_relation_length = self.config.get('max_relation_length', 8)
    
    def normalize_node_name(self, name: str) -> str:
        """
        规范化节点名称
        规则：
        1. 移除多余空格和标点
        2. 截断过长名称（保留核心词）
        3. 统一格式（去除书名号等）
        
        Args:
            name: 原始节点名称
            
        Returns:
            规范化后的节点名称
        """
        if not name or not isinstance(name, str):
            return name
        
        normalized = name.strip()
        
        # 移除书名号，但保留内容
        normalized = re.sub(r'[《》]', '', normalized)
        
        # 移除引号
        normalized = re.sub(r'["""'']', '', normalized)
        
        # 移除多余空格
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # 如果太长，尝试提取核心词
        if len(normalized) > self.max_node_name_length:
            # 中文：取前N个字
            if re.search(r'[\u4e00-\u9fa5]', normalized):
                normalized = normalized[:self.max_node_name_length]
            else:
                # 英文：取前几个词
                words = normalized.split()
                if len(words) > 1:
                    normalized = ' '.join(words[:2])
                else:
                    normalized = normalized[:self.max_node_name_length]
        
        return normalized
    
    def infer_node_type(self, node: Dict) -> str:
        """
        推断节点类型
        基于名称和描述推断节点类型
        
        Args:
            node: 节点字典，包含 label, id, description, type 等字段
            
        Returns:
            节点类型字符串
        """
        name = (node.get('label') or node.get('id') or '').lower()
        description = (node.get('description') or '').lower()
        existing_type = node.get('type') or node.get('entity_type') or ''
        
        # 如果已有明确类型，先检查是否符合标准
        if existing_type and existing_type in self.node_types:
            return existing_type
        
        # 基于名称和描述推断
        text = name + ' ' + description
        
        # 检查是否是人名（简单启发式规则）
        if self._is_person_name(name):
            return 'Person'
        
        # 检查是否是书籍
        if any(word in text for word in ['书', 'book', '著作', '作品']):
            return 'Book'
        
        # 检查是否是策略/方法
        if any(word in text for word in ['策略', '方法', 'strategy', 'method']):
            return 'Strategy'
        
        # 检查是否是概念
        if any(word in text for word in ['概念', '理念', 'concept', 'idea']):
            return 'Concept'
        
        # 检查是否是群体
        if any(word in text for word in ['群体', '人群', 'group', 'people']):
            return 'Group'
        
        # 默认返回 Entity
        return 'Entity'
    
    def _is_person_name(self, name: str) -> bool:
        """
        简单的人名检测（中文）
        
        Args:
            name: 名称字符串
            
        Returns:
            是否可能是人名
        """
        # 中文人名通常是2-4个字，且不包含常见非人名词汇
        if re.search(r'[\u4e00-\u9fa5]', name):
            length = len(name)
            if 2 <= length <= 4:
                # 排除常见非人名词汇
                exclude_words = ['书', '方法', '策略', '概念', '基金', '指数', '投资']
                return not any(word in name for word in exclude_words)
        return False
    
    def normalize_relation(self, relation: str) -> str:
        """
        规范化关系名称
        映射到标准关系词表
        
        Args:
            relation: 原始关系名称
            
        Returns:
            规范化后的关系名称
        """
        if not relation or not isinstance(relation, str):
            return '相关'
        
        normalized = relation.strip()
        
        # 直接匹配
        if normalized in self.standard_relations:
            return self.standard_relations[normalized]
        
        # 模糊匹配（包含关系）
        for key, value in self.standard_relations.items():
            if key in normalized or normalized in key:
                return value
        
        # 如果太长，截断
        if len(normalized) > self.max_relation_length:
            return normalized[:self.max_relation_length]
        
        # 默认返回原值（如果很短）
        return normalized if len(normalized) <= self.max_relation_length else '相关'
    
    def extract_properties(self, node: Dict) -> Tuple[str, Dict]:
        """
        提取属性（从描述中分离出属性信息）
        将长描述中的具体信息提取为属性，保留简短描述
        
        Args:
            node: 节点字典
            
        Returns:
            (简短描述, 属性字典) 元组
        """
        description = node.get('description', '')
        properties = node.get('properties', {}) or {}
        
        # 如果描述太长，尝试提取关键信息
        if len(description) > 50:
            # 提取数字信息
            numbers = re.findall(r'\d+[万千百十]?', description)
            if numbers:
                properties['numbers'] = numbers
            
            # 提取时间信息
            time_patterns = [
                r'\d+年',
                r'\d+月',
                r'\d+天',
                r'长期|短期|中期'
            ]
            times = []
            for pattern in time_patterns:
                matches = re.findall(pattern, description)
                if matches:
                    times.extend(matches)
            if times:
                properties['times'] = times
            
            # 简化描述（保留前50字）
            short_description = description[:50] + '...'
            return short_description, properties
        
        return description, properties
    
    def merge_duplicate_nodes(self, nodes: List[Dict]) -> Tuple[List[Dict], Dict[str, str]]:
        """
        合并重复节点
        基于名称相似度合并重复节点
        
        Args:
            nodes: 节点列表
            
        Returns:
            (合并后的节点列表, 别名映射字典) 元组
        """
        node_map = {}
        aliases = {}  # 别名映射
        
        for node in nodes:
            normalized_name = self.normalize_node_name(node.get('id') or node.get('label', ''))
            
            # 检查是否已存在相似节点
            existing_key = None
            for key in node_map.keys():
                if self._is_similar_node(normalized_name, key):
                    existing_key = key
                    aliases[normalized_name] = key
                    break
            
            if existing_key:
                # 合并节点
                existing_node = node_map[existing_key]
                existing_node['degree'] = max(existing_node.get('degree', 0), node.get('degree', 0))
                if node.get('description') and not existing_node.get('description'):
                    existing_node['description'] = node.get('description')
                if node.get('properties'):
                    existing_props = existing_node.get('properties', {}) or {}
                    existing_props.update(node.get('properties', {}))
                    existing_node['properties'] = existing_props
            else:
                # 创建新节点
                normalized = self.normalize_node(node)
                node_map[normalized_name] = normalized
        
        return list(node_map.values()), aliases
    
    def _is_similar_node(self, name1: str, name2: str) -> bool:
        """
        检查两个节点名称是否相似
        
        Args:
            name1: 第一个节点名称
            name2: 第二个节点名称
            
        Returns:
            是否相似
        """
        if name1 == name2:
            return True
        
        # 移除常见修饰词后比较
        clean1 = re.sub(r'[《》""'' \t\n]', '', name1)
        clean2 = re.sub(r'[《》""'' \t\n]', '', name2)
        
        if clean1 == clean2:
            return True
        
        # 检查是否一个包含另一个
        if clean1 in clean2 or clean2 in clean1:
            return abs(len(clean1) - len(clean2)) <= 3  # 长度差不超过3
        
        return False
    
    def normalize_node(self, node: Dict) -> Dict:
        """
        规范化单个节点
        
        Args:
            node: 原始节点字典
            
        Returns:
            规范化后的节点字典
        """
        normalized_name = self.normalize_node_name(node.get('id') or node.get('label', ''))
        node_type = self.infer_node_type(node)
        description, properties = self.extract_properties(node)
        
        # 获取原始数据（避免嵌套）
        original_data = node.get('original') or {
            k: v for k, v in node.items() if k != 'original'
        }

        return {
            'id': normalized_name,
            'label': normalized_name,
            'type': node_type,
            'description': description,
            'properties': properties,
            'degree': node.get('degree', 0),
            'original': original_data
        }
    
    def normalize_edge(self, edge: Dict, node_aliases: Dict[str, str] = None) -> Dict:
        """
        规范化关系（边）
        
        Args:
            edge: 原始边字典
            node_aliases: 节点别名映射
            
        Returns:
            规范化后的边字典
        """
        node_aliases = node_aliases or {}
        
        source = self.normalize_node_name(edge.get('source') or edge.get('src_id') or edge.get('from', ''))
        target = self.normalize_node_name(edge.get('target') or edge.get('tgt_id') or edge.get('to', ''))
        
        # 应用别名映射
        normalized_source = node_aliases.get(source, source)
        normalized_target = node_aliases.get(target, target)
        
        relation = self.normalize_relation(
            edge.get('label') or
            edge.get('relation') or
            (edge.get('properties', {}) or {}).get('description', '') or
            edge.get('description', '') or
            '相关'
        )
        
        # 获取原始数据（避免嵌套）
        original_data = edge.get('original') or {
            k: v for k, v in edge.items() if k != 'original'
        }

        return {
            'source': normalized_source,
            'target': normalized_target,
            'label': relation,
            'weight': edge.get('weight') or (edge.get('properties', {}) or {}).get('weight', 1),
            'original': original_data
        }
    
    def normalize_graph(self, graph_data: Dict) -> Dict:
        """
        规范化整个知识图谱
        这是主要的入口方法
        
        Args:
            graph_data: 原始知识图谱数据，格式为 {'nodes': [...], 'edges': [...]}
            
        Returns:
            规范化后的知识图谱数据，包含统计信息
        """
        if not graph_data or (not graph_data.get('nodes') and not graph_data.get('edges')):
            return {'nodes': [], 'edges': [], 'stats': {}}
        
        # 1. 规范化节点
        raw_nodes = [self.normalize_node(node) for node in (graph_data.get('nodes') or [])]
        
        # 2. 合并重复节点
        nodes, aliases = self.merge_duplicate_nodes(raw_nodes)
        
        # 3. 规范化边
        raw_edges = graph_data.get('edges') or []
        edges = []
        for edge in raw_edges:
            normalized_edge = self.normalize_edge(edge, aliases)
            # 过滤掉无效边（源或目标为空，或源等于目标）
            if normalized_edge['source'] and normalized_edge['target'] and \
               normalized_edge['source'] != normalized_edge['target']:
                edges.append(normalized_edge)
        
        # 4. 重新计算节点度数
        node_map = {node['id']: node for node in nodes}
        for edge in edges:
            if edge['source'] in node_map:
                node_map[edge['source']]['degree'] = node_map[edge['source']].get('degree', 0) + 1
            if edge['target'] in node_map:
                node_map[edge['target']]['degree'] = node_map[edge['target']].get('degree', 0) + 1
        
        return {
            'nodes': list(node_map.values()),
            'edges': edges,
            'stats': {
                'original_nodes': len(graph_data.get('nodes', [])),
                'normalized_nodes': len(nodes),
                'original_edges': len(raw_edges),
                'normalized_edges': len(edges)
            }
        }
