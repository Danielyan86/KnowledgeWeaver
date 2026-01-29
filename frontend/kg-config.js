/**
 * Knowledge Graph Configuration
 * 知识图谱配置文件
 * 
 * 定义节点类型、关系词表、可视化配置等
 */

const KG_CONFIG = {
    // 节点类型定义（用于分类和颜色映射）
    NODE_TYPES: {
        'Person': {
            label: {
                zh: '人物',
                en: 'Person'
            },
            color: '#FF6B6B',
            icon: '👤'
        },
        'Book': {
            label: {
                zh: '书籍',
                en: 'Book'
            },
            color: '#4ECDC4',
            icon: '📚'
        },
        'Concept': {
            label: {
                zh: '概念',
                en: 'Concept'
            },
            color: '#45B7D1',
            icon: '💡'
        },
        'Strategy': {
            label: {
                zh: '策略',
                en: 'Strategy'
            },
            color: '#96CEB4',
            icon: '📊'
        },
        'Metric': {
            label: {
                zh: '指标',
                en: 'Metric'
            },
            color: '#FFEAA7',
            icon: '📈'
        },
        'Example': {
            label: {
                zh: '示例',
                en: 'Example'
            },
            color: '#DDA0DD',
            icon: '💬'
        },
        'Group': {
            label: {
                zh: '群体',
                en: 'Group'
            },
            color: '#98D8C8',
            icon: '👥'
        },
        'Entity': {
            label: {
                zh: '实体',
                en: 'Entity'
            },
            color: '#95A5A6',
            icon: '🔷'
        }
    },

    // 标准关系词表（可提问、可复用）
    STANDARD_RELATIONS: {
        // 创作关系
        '著作': { label: '著作', category: '创作', question: '谁著作了{target}？' },
        '编写': { label: '著作', category: '创作', question: '谁编写了{target}？' },
        '撰写': { label: '著作', category: '创作', question: '谁撰写了{target}？' },
        '创作': { label: '著作', category: '创作', question: '谁创作了{target}？' },
        '出版': { label: '著作', category: '创作', question: '谁出版了{target}？' },
        
        // 主张/观点关系
        '主张': { label: '主张', category: '观点', question: '{source}主张什么？' },
        '强调': { label: '主张', category: '观点', question: '{source}强调什么？' },
        '提倡': { label: '主张', category: '观点', question: '{source}提倡什么？' },
        '倡导': { label: '主张', category: '观点', question: '{source}倡导什么？' },
        '认为': { label: '主张', category: '观点', question: '{source}认为什么？' },
        
        // 包含/属于关系
        '属于': { label: '属于', category: '层级', question: '{source}属于什么？' },
        '包含': { label: '包含', category: '层级', question: '{source}包含什么？' },
        '涵盖': { label: '包含', category: '层级', question: '{source}涵盖什么？' },
        '包括': { label: '包含', category: '层级', question: '{source}包括什么？' },
        
        // 适用关系
        '适用于': { label: '适用于', category: '应用', question: '{source}适用于谁？' },
        '适合': { label: '适用于', category: '应用', question: '{source}适合谁？' },
        '针对': { label: '适用于', category: '应用', question: '{source}针对谁？' },
        '面向': { label: '适用于', category: '应用', question: '{source}面向谁？' },
        
        // 影响关系
        '影响': { label: '影响', category: '因果', question: '{source}影响什么？' },
        '导致': { label: '影响', category: '因果', question: '{source}导致什么？' },
        '产生': { label: '影响', category: '因果', question: '{source}产生什么？' },
        '带来': { label: '影响', category: '因果', question: '{source}带来什么？' },
        
        // 依赖关系
        '依赖': { label: '依赖', category: '依赖', question: '{source}依赖什么？' },
        '基于': { label: '依赖', category: '依赖', question: '{source}基于什么？' },
        '建立在': { label: '依赖', category: '依赖', question: '{source}建立在什么基础上？' },
        '需要': { label: '依赖', category: '依赖', question: '{source}需要什么？' },
        
        // 推荐关系
        '推荐': { label: '推荐', category: '推荐', question: '{source}推荐什么？' },
        '建议': { label: '推荐', category: '推荐', question: '{source}建议什么？' },
        '推荐标的': { label: '推荐', category: '推荐', question: '{source}推荐什么标的？' },
        '推荐工具': { label: '推荐', category: '推荐', question: '{source}推荐什么工具？' },
        
        // 特征关系
        '特点': { label: '特点', category: '属性', question: '{source}有什么特点？' },
        '特征': { label: '特点', category: '属性', question: '{source}有什么特征？' },
        '关键特征': { label: '特点', category: '属性', question: '{source}的关键特征是什么？' },
        '属性': { label: '特点', category: '属性', question: '{source}有什么属性？' },
        
        // 对比关系
        '对比': { label: '对比', category: '对比', question: '{source}与什么对比？' },
        '相比': { label: '对比', category: '对比', question: '{source}与什么相比？' },
        '区别': { label: '对比', category: '对比', question: '{source}与什么有区别？' },
        
        // 反例关系
        '反例': { label: '反例', category: '反例', question: '{source}的反例是什么？' },
        '反面': { label: '反例', category: '反例', question: '{source}的反面是什么？' },
        '不推荐': { label: '反例', category: '反例', question: '{source}不推荐什么？' }
    },

    // 可视化配置
    VISUALIZATION: {
        // 节点配置
        NODE: {
            MIN_RADIUS: 8,
            MAX_RADIUS: 25,
            STROKE_WIDTH: 2,
            STROKE_COLOR: '#fff',
            LABEL_FONT_SIZE_MIN: 10,
            LABEL_FONT_SIZE_MAX: 14,
            MAX_LABEL_LENGTH: 10 // 节点标签最大长度
        },
        
        // 边配置
        EDGE: {
            STROKE_COLOR: '#aaa',
            STROKE_OPACITY: 0.5,
            STROKE_WIDTH_MIN: 1,
            STROKE_WIDTH_MAX: 2,
            LABEL_FONT_SIZE: 9,
            MAX_LABEL_LENGTH: 12, // 关系标签最大长度
            ARROW_SIZE: 4
        },
        
        // 布局配置
        LAYOUT: {
            LINK_DISTANCE: 80,
            CHARGE_STRENGTH: -300,
            COLLISION_RADIUS: 30,
            CENTER_STRENGTH: 0.05
        }
    },

    // 数据质量配置
    QUALITY: {
        MAX_NODE_NAME_LENGTH: 10, // 节点名称最大长度
        MAX_RELATION_LENGTH: 8,   // 关系名称最大长度
        MIN_NODE_DEGREE: 0,       // 最小节点度数（用于过滤孤立节点）
        MAX_DESCRIPTION_LENGTH: 50 // 描述最大长度
    }
};

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = KG_CONFIG;
} else {
    window.KG_CONFIG = KG_CONFIG;
}
