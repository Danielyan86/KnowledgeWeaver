"""
Prompt Manager - Jinja 模板管理器
使用 Jinja2 管理提示词模板

优势：
1. 模板与代码分离，非开发人员可直接编辑
2. 支持条件、循环、过滤器
3. 支持模板继承和复用
4. 配置驱动，易于扩展
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


class PromptManager:
    """提示词模板管理器"""

    def __init__(self, template_dir: str = None):
        """
        初始化模板管理器

        Args:
            template_dir: 模板目录路径，默认为 backend/prompts
        """
        if template_dir is None:
            template_dir = Path(__file__).parent / "prompts"

        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)

        # 初始化 Jinja 环境
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # 添加自定义过滤器
        self.env.filters['tojson'] = lambda x, **kwargs: json.dumps(
            x, ensure_ascii=False, **kwargs
        )

        # 默认配置
        self.default_config = self._load_default_config()

    def _load_default_config(self) -> Dict:
        """加载默认配置"""
        return {
            "max_entity_length": 10,
            "max_relation_length": 4,
            "entity_types": {
                "Person": {"description": "人物（作者、投资者、创始人等）"},
                "Book": {"description": "书籍（书名、著作、作品）"},
                "Concept": {"description": "概念（理念、理论、原理）"},
                "Strategy": {"description": "策略（投资策略、方法、方案）"},
                "Metric": {"description": "指标（数据、数值、统计）"},
                "Group": {"description": "群体（人群、用户群体）"},
                "Entity": {"description": "其他实体"}
            },
            "standard_relations": {
                "创作类": ["著作", "编写", "撰写"],
                "观点类": ["主张", "强调", "提倡", "认为"],
                "层级类": ["属于", "包含", "涵盖"],
                "应用类": ["适用于", "适合", "针对"],
                "因果类": ["影响", "导致", "产生"],
                "依赖类": ["依赖", "基于", "需要"],
                "推荐类": ["推荐", "建议"],
                "属性类": ["特点", "特征"],
                "对比类": ["对比", "区别"],
                "反例类": ["反例", "不推荐"]
            },
            "examples": [
                {
                    "input": "李笑来在《让时间陪你慢慢变富》中主张定投策略。",
                    "output": {
                        "entities": [
                            {"name": "李笑来", "type": "Person", "description": "投资者、作家"},
                            {"name": "让时间陪你慢慢变富", "type": "Book", "description": "投资理财书籍"},
                            {"name": "定投", "type": "Strategy", "description": "定期定额投资策略"}
                        ],
                        "relations": [
                            {"source": "李笑来", "relation": "著作", "target": "让时间陪你慢慢变富"},
                            {"source": "让时间陪你慢慢变富", "relation": "主张", "target": "定投"}
                        ]
                    }
                }
            ]
        }

    def render(
        self,
        template_name: str,
        text: str,
        config: Optional[Dict] = None,
        **kwargs
    ) -> str:
        """
        渲染提示词模板

        Args:
            template_name: 模板名称（如 "extraction.j2"）
            text: 待处理的文本
            config: 自定义配置（覆盖默认配置）
            **kwargs: 额外的模板变量

        Returns:
            渲染后的提示词字符串
        """
        # 合并配置
        merged_config = {**self.default_config}
        if config:
            merged_config.update(config)

        # 加载并渲染模板
        template = self.env.get_template(template_name)
        return template.render(
            text=text,
            **merged_config,
            **kwargs
        )

    def get_extraction_prompt(
        self,
        text: str,
        domain: Optional[str] = None,
        custom_types: Optional[Dict] = None,
        custom_relations: Optional[Dict] = None
    ) -> str:
        """
        获取知识图谱提取提示词

        Args:
            text: 待提取的文本
            domain: 领域（用于加载领域特定配置）
            custom_types: 自定义实体类型
            custom_relations: 自定义关系类型

        Returns:
            完整的提示词字符串
        """
        config = {}

        # 加载领域配置
        if domain:
            domain_config = self._load_domain_config(domain)
            config.update(domain_config)

        # 应用自定义配置
        if custom_types:
            config["entity_types"] = custom_types
        if custom_relations:
            config["standard_relations"] = custom_relations

        return self.render("extraction.j2", text, config)

    def _load_domain_config(self, domain: str) -> Dict:
        """
        加载领域特定配置

        Args:
            domain: 领域名称

        Returns:
            领域配置字典
        """
        config_file = self.template_dir / f"{domain}_config.json"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def list_templates(self) -> List[str]:
        """列出所有可用模板"""
        return [f.name for f in self.template_dir.glob("*.j2")]

    def create_domain_config(
        self,
        domain: str,
        entity_types: Dict,
        standard_relations: Dict,
        examples: Optional[List] = None
    ) -> None:
        """
        创建领域配置文件

        Args:
            domain: 领域名称
            entity_types: 实体类型定义
            standard_relations: 标准关系定义
            examples: 示例列表
        """
        config = {
            "entity_types": entity_types,
            "standard_relations": standard_relations,
            "examples": examples or []
        }

        config_file = self.template_dir / f"{domain}_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)


# 单例实例
_prompt_manager = None


def get_prompt_manager(template_dir: str = None) -> PromptManager:
    """获取提示词管理器实例（单例）"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager(template_dir)
    return _prompt_manager


# 便捷函数（兼容旧接口）
def get_extraction_prompt(text: str, **kwargs) -> str:
    """获取知识图谱提取提示词（兼容旧接口）"""
    return get_prompt_manager().get_extraction_prompt(text, **kwargs)


# 命令行测试
if __name__ == "__main__":
    manager = PromptManager()

    # 测试渲染
    test_text = "李笑来在《让时间陪你慢慢变富》中主张定投策略。"
    prompt = manager.get_extraction_prompt(test_text)

    print("=" * 60)
    print("渲染后的提示词：")
    print("=" * 60)
    print(prompt)
    print("=" * 60)
    print(f"\n可用模板: {manager.list_templates()}")
