"""
Prompt Loader
从 Markdown 文件加载提示词

支持：
- 从 .md 文件读取提示词
- 模板变量替换
- 缓存机制
"""

import os
from pathlib import Path
from typing import Dict, Optional


class PromptLoader:
    """Markdown 提示词加载器"""

    def __init__(self, prompts_dir: Path = None):
        """
        初始化加载器

        Args:
            prompts_dir: 提示词目录路径
        """
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent

        self.prompts_dir = Path(prompts_dir)
        self._cache = {}

    def load_prompt(self, filename: str, **kwargs) -> str:
        """
        从 Markdown 文件加载提示词并替换变量

        Args:
            filename: 文件名（如 'extraction.md'）
            **kwargs: 模板变量

        Returns:
            渲染后的提示词
        """
        # 从缓存或文件加载模板
        if filename not in self._cache:
            file_path = self.prompts_dir / filename
            if not file_path.exists():
                raise FileNotFoundError(f"提示词文件不存在: {file_path}")

            with open(file_path, 'r', encoding='utf-8') as f:
                template = f.read()

            # 缓存模板
            self._cache[filename] = template
        else:
            template = self._cache[filename]

        # 替换变量
        return template.format(**kwargs)

    def clear_cache(self):
        """清空缓存（用于重新加载修改后的提示词）"""
        self._cache.clear()


# 全局实例
_loader = PromptLoader()


def load_prompt(filename: str, **kwargs) -> str:
    """
    加载提示词（便捷函数）

    Args:
        filename: 文件名（如 'extraction.md'）
        **kwargs: 模板变量

    Returns:
        渲染后的提示词
    """
    return _loader.load_prompt(filename, **kwargs)


def get_extraction_prompt(text: str) -> str:
    """
    获取知识图谱提取提示词（兼容旧接口）

    Args:
        text: 待提取的文本

    Returns:
        完整的提示词字符串
    """
    return load_prompt('extraction.md', text=text)


def get_document_topic_prompt(sample: str) -> str:
    """
    获取文档主题提取提示词

    Args:
        sample: 文档样本（前 1000 字）

    Returns:
        完整的提示词字符串
    """
    return load_prompt('document_topic.md', sample=sample)


# 命令行测试
if __name__ == "__main__":
    # 测试提取提示词
    test_text = "李笑来在《让时间陪你慢慢变富》中主张定投策略。"
    prompt = get_extraction_prompt(test_text)

    print("=" * 60)
    print("提取提示词：")
    print("=" * 60)
    print(prompt)
    print("=" * 60)

    # 测试主题提示词
    print("\n主题提示词：")
    print("=" * 60)
    topic_prompt = get_document_topic_prompt("这是一本关于投资的书...")
    print(topic_prompt)
    print("=" * 60)
