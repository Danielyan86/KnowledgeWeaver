/**
 * Knowledge Graph Normalizer
 * 知识图谱规范化模块
 * 
 * 核心功能：
 * 1. 节点名称规范化（缩短、去重、合并）
 * 2. 节点类型标准化
 * 3. 关系词规范化（映射到标准关系词表）
 * 4. 属性提取和分离
 */

class KnowledgeGraphNormalizer {
    constructor(config = {}) {
        // 节点类型定义
        this.nodeTypes = config.nodeTypes || {
            'Person': ['人', '作者', '作家', '投资者', '创始人'],
            'Book': ['书', '书籍', '著作', '作品'],
            'Concept': ['概念', '理念', '方法', '策略', '理论'],
            'Strategy': ['策略', '方法', '投资策略', '理财方法'],
            'Metric': ['指标', '数据', '数值', '统计'],
            'Example': ['例子', '案例', '实例', '示例'],
            'Group': ['群体', '人群', '投资者', '普通人'],
            'Entity': ['实体', '对象'] // 默认类型
        };

        // 标准关系词表（可提问、可复用）
        this.standardRelations = config.standardRelations || {
            // 创作关系
            '著作': '著作',
            '编写': '著作',
            '撰写': '著作',
            '创作': '著作',
            '出版': '著作',
            
            // 主张/观点关系
            '主张': '主张',
            '强调': '主张',
            '提倡': '主张',
            '倡导': '主张',
            '认为': '主张',
            '观点': '主张',
            
            // 包含/属于关系
            '属于': '属于',
            '包含': '包含',
            '涵盖': '包含',
            '包括': '包含',
            '组成': '包含',
            
            // 适用关系
            '适用于': '适用于',
            '适合': '适用于',
            '针对': '适用于',
            '面向': '适用于',
            
            // 影响关系
            '影响': '影响',
            '导致': '影响',
            '产生': '影响',
            '带来': '影响',
            
            // 依赖关系
            '依赖': '依赖',
            '基于': '依赖',
            '建立在': '依赖',
            '需要': '依赖',
            
            // 对比关系
            '对比': '对比',
            '相比': '对比',
            '区别': '对比',
            '不同': '对比',
            
            // 推荐关系
            '推荐': '推荐',
            '建议': '推荐',
            '推荐标的': '推荐',
            '推荐工具': '推荐',
            
            // 特征关系
            '特点': '特点',
            '特征': '特点',
            '关键特征': '特点',
            '属性': '特点',
            
            // 反例关系
            '反例': '反例',
            '反面': '反例',
            '不推荐': '反例'
        };

        // 节点名称最大长度
        this.maxNodeNameLength = config.maxNodeNameLength || 10;
        
        // 关系名称最大长度
        this.maxRelationLength = config.maxRelationLength || 8;
    }

    /**
     * 规范化节点名称
     * 规则：
     * 1. 移除多余空格和标点
     * 2. 截断过长名称（保留核心词）
     * 3. 统一格式（去除书名号等）
     */
    normalizeNodeName(name) {
        if (!name || typeof name !== 'string') return name;
        
        let normalized = name.trim();
        
        // 移除书名号，但保留内容
        normalized = normalized.replace(/[《》]/g, '');
        
        // 移除引号
        normalized = normalized.replace(/["""'']/g, '');
        
        // 移除多余空格
        normalized = normalized.replace(/\s+/g, ' ').trim();
        
        // 如果太长，尝试提取核心词
        if (normalized.length > this.maxNodeNameLength) {
            // 尝试提取前几个字（中文）或前几个词（英文）
            if (/[\u4e00-\u9fa5]/.test(normalized)) {
                // 中文：取前N个字
                normalized = normalized.substring(0, this.maxNodeNameLength);
            } else {
                // 英文：取前几个词
                const words = normalized.split(/\s+/);
                if (words.length > 1) {
                    normalized = words.slice(0, 2).join(' ');
                } else {
                    normalized = normalized.substring(0, this.maxNodeNameLength);
                }
            }
        }
        
        return normalized;
    }

    /**
     * 推断节点类型
     * 基于名称和描述推断节点类型
     */
    inferNodeType(node) {
        const name = (node.label || node.id || '').toLowerCase();
        const description = (node.description || '').toLowerCase();
        const existingType = node.type || node.entity_type || '';
        
        // 如果已有明确类型，先检查是否符合标准
        if (existingType && this.nodeTypes[existingType]) {
            return existingType;
        }
        
        // 基于名称和描述推断
        const text = name + ' ' + description;
        
        // 检查是否是人名（简单启发式规则）
        if (this.isPersonName(name)) {
            return 'Person';
        }
        
        // 检查是否是书籍
        if (text.includes('书') || text.includes('book') || 
            text.includes('著作') || text.includes('作品')) {
            return 'Book';
        }
        
        // 检查是否是策略/方法
        if (text.includes('策略') || text.includes('方法') || 
            text.includes('strategy') || text.includes('method')) {
            return 'Strategy';
        }
        
        // 检查是否是概念
        if (text.includes('概念') || text.includes('理念') || 
            text.includes('concept') || text.includes('idea')) {
            return 'Concept';
        }
        
        // 检查是否是群体
        if (text.includes('群体') || text.includes('人群') || 
            text.includes('group') || text.includes('people')) {
            return 'Group';
        }
        
        // 默认返回 Entity
        return 'Entity';
    }

    /**
     * 简单的人名检测（中文）
     */
    isPersonName(name) {
        // 中文人名通常是2-4个字，且不包含常见非人名词汇
        if (/[\u4e00-\u9fa5]/.test(name)) {
            const length = name.length;
            if (length >= 2 && length <= 4) {
                // 排除常见非人名词汇
                const excludeWords = ['书', '方法', '策略', '概念', '基金', '指数', '投资'];
                return !excludeWords.some(word => name.includes(word));
            }
        }
        return false;
    }

    /**
     * 规范化关系名称
     * 映射到标准关系词表
     */
    normalizeRelation(relation) {
        if (!relation || typeof relation !== 'string') return '相关';
        
        const normalized = relation.trim();
        
        // 直接匹配
        if (this.standardRelations[normalized]) {
            return this.standardRelations[normalized];
        }
        
        // 模糊匹配（包含关系）
        for (const [key, value] of Object.entries(this.standardRelations)) {
            if (normalized.includes(key) || key.includes(normalized)) {
                return value;
            }
        }
        
        // 如果太长，截断
        if (normalized.length > this.maxRelationLength) {
            return normalized.substring(0, this.maxRelationLength);
        }
        
        // 默认返回原值（如果很短）
        return normalized.length <= this.maxRelationLength ? normalized : '相关';
    }

    /**
     * 提取属性（从描述中分离出属性信息）
     * 将长描述中的具体信息提取为属性，保留简短描述
     */
    extractProperties(node) {
        const description = node.description || '';
        const properties = node.properties || {};
        
        // 如果描述太长，尝试提取关键信息
        if (description.length > 50) {
            // 提取数字信息
            const numbers = description.match(/\d+[万千百十]?/g);
            if (numbers) {
                properties.numbers = numbers;
            }
            
            // 提取时间信息
            const timePatterns = [
                /\d+年/g,
                /\d+月/g,
                /\d+天/g,
                /长期|短期|中期/g
            ];
            const times = [];
            timePatterns.forEach(pattern => {
                const matches = description.match(pattern);
                if (matches) times.push(...matches);
            });
            if (times.length > 0) {
                properties.times = times;
            }
            
            // 简化描述（保留前50字）
            const shortDescription = description.substring(0, 50) + '...';
            return {
                description: shortDescription,
                properties: properties
            };
        }
        
        return {
            description: description,
            properties: properties
        };
    }

    /**
     * 合并重复节点
     * 基于名称相似度合并重复节点
     */
    mergeDuplicateNodes(nodes) {
        const nodeMap = new Map();
        const aliases = new Map(); // 别名映射
        
        nodes.forEach(node => {
            const normalizedName = this.normalizeNodeName(node.id || node.label);
            
            // 检查是否已存在相似节点
            let existingNode = null;
            for (const [key, value] of nodeMap.entries()) {
                if (this.isSimilarNode(normalizedName, key)) {
                    existingNode = value;
                    aliases.set(normalizedName, key);
                    break;
                }
            }
            
            if (existingNode) {
                // 合并节点
                existingNode.degree = Math.max(existingNode.degree, node.degree || 0);
                if (node.description && !existingNode.description) {
                    existingNode.description = node.description;
                }
                if (node.properties) {
                    existingNode.properties = { ...existingNode.properties, ...node.properties };
                }
            } else {
                // 创建新节点
                const normalized = this.normalizeNode(node);
                nodeMap.set(normalizedName, normalized);
            }
        });
        
        return {
            nodes: Array.from(nodeMap.values()),
            aliases: aliases
        };
    }

    /**
     * 检查两个节点名称是否相似
     */
    isSimilarNode(name1, name2) {
        if (name1 === name2) return true;
        
        // 移除常见修饰词后比较
        const clean1 = name1.replace(/[《》""''\s]/g, '');
        const clean2 = name2.replace(/[《》""''\s]/g, '');
        
        if (clean1 === clean2) return true;
        
        // 检查是否一个包含另一个
        if (clean1.includes(clean2) || clean2.includes(clean1)) {
            return Math.abs(clean1.length - clean2.length) <= 3; // 长度差不超过3
        }
        
        return false;
    }

    /**
     * 规范化单个节点
     */
    normalizeNode(node) {
        const normalizedName = this.normalizeNodeName(node.id || node.label || '');
        const nodeType = this.inferNodeType(node);
        const { description, properties } = this.extractProperties(node);
        
        return {
            id: normalizedName,
            label: normalizedName,
            type: nodeType,
            description: description,
            properties: properties,
            degree: node.degree || 0,
            original: node // 保留原始数据
        };
    }

    /**
     * 规范化关系（边）
     */
    normalizeEdge(edge, nodeAliases = new Map()) {
        const source = this.normalizeNodeName(edge.source || edge.src_id || edge.from || '');
        const target = this.normalizeNodeName(edge.target || edge.tgt_id || edge.to || '');
        
        // 应用别名映射
        const normalizedSource = nodeAliases.get(source) || source;
        const normalizedTarget = nodeAliases.get(target) || target;
        
        const relation = this.normalizeRelation(
            edge.label || 
            edge.relation || 
            edge.properties?.description || 
            edge.description || 
            '相关'
        );
        
        return {
            source: normalizedSource,
            target: normalizedTarget,
            label: relation,
            weight: edge.weight || edge.properties?.weight || 1,
            original: edge // 保留原始数据
        };
    }

    /**
     * 规范化整个知识图谱
     * 这是主要的入口方法
     */
    normalizeGraph(graphData) {
        if (!graphData || (!graphData.nodes && !graphData.edges)) {
            return { nodes: [], edges: [] };
        }
        
        // 1. 规范化节点
        const rawNodes = (graphData.nodes || []).map(node => this.normalizeNode(node));
        
        // 2. 合并重复节点
        const { nodes, aliases } = this.mergeDuplicateNodes(rawNodes);
        
        // 3. 规范化边
        const rawEdges = graphData.edges || [];
        const edges = rawEdges
            .map(edge => this.normalizeEdge(edge, aliases))
            .filter(edge => {
                // 过滤掉无效边（源或目标为空，或源等于目标）
                return edge.source && edge.target && edge.source !== edge.target;
            });
        
        // 4. 重新计算节点度数
        const nodeMap = new Map(nodes.map(n => [n.id, n]));
        edges.forEach(edge => {
            if (nodeMap.has(edge.source)) {
                nodeMap.get(edge.source).degree++;
            }
            if (nodeMap.has(edge.target)) {
                nodeMap.get(edge.target).degree++;
            }
        });
        
        return {
            nodes: Array.from(nodeMap.values()),
            edges: edges,
            stats: {
                originalNodes: graphData.nodes?.length || 0,
                normalizedNodes: nodes.length,
                originalEdges: rawEdges.length,
                normalizedEdges: edges.length
            }
        };
    }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = KnowledgeGraphNormalizer;
} else {
    window.KnowledgeGraphNormalizer = KnowledgeGraphNormalizer;
}
