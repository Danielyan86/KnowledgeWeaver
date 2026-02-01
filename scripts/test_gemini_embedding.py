#!/usr/bin/env python3
"""
测试 Gemini Embedding 服务
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.core.embeddings.service import get_embedding_service


def main():
    print("=" * 60)
    print("测试 Gemini Embedding 服务")
    print("=" * 60)

    # 获取服务实例
    service = get_embedding_service()

    # 测试单个文本
    print("\n1. 测试单个文本 embedding:")
    test_text = "李笑来是一位投资人和作家"
    embedding = service.embed_text(test_text)

    if embedding:
        print(f"✅ 成功生成 embedding")
        print(f"   文本: {test_text}")
        print(f"   维度: {len(embedding)}")
        print(f"   前5个值: {embedding[:5]}")
    else:
        print(f"❌ 生成 embedding 失败")
        return

    # 测试批量文本
    print("\n2. 测试批量 embedding:")
    test_texts = [
        "定投是一种投资策略",
        "长期主义强调时间的复利",
        "普通人适合定投指数基金",
        "比特币是一种数字货币"
    ]

    embeddings = service.embed_texts(test_texts)

    if embeddings and all(embeddings):
        print(f"✅ 成功生成批量 embedding")
        print(f"   文本数量: {len(test_texts)}")
        print(f"   embedding 数量: {len(embeddings)}")
        print(f"   每个维度: {len(embeddings[0])}")
        print(f"   缓存大小: {service.get_cache_size()}")
    else:
        print(f"❌ 批量 embedding 失败")
        return

    # 测试缓存
    print("\n3. 测试缓存:")
    embedding2 = service.embed_text(test_text)  # 应该从缓存读取

    if embedding == embedding2:
        print(f"✅ 缓存工作正常")
    else:
        print(f"❌ 缓存异常")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
