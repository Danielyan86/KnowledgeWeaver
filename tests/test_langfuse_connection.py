#!/usr/bin/env python3
"""
Langfuse 连接测试脚本

使用方法：
1. 确保已配置 .env 文件中的 Langfuse 相关变量
2. 运行: python test_langfuse_connection.py
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_langfuse_connection():
    """测试 Langfuse 连接"""
    print("=" * 60)
    print("Langfuse 连接测试")
    print("=" * 60)

    # 检查环境变量
    enabled = os.getenv('LANGFUSE_ENABLED', 'false').lower() == 'true'
    host = os.getenv('LANGFUSE_HOST', '')
    public_key = os.getenv('LANGFUSE_PUBLIC_KEY', '')
    secret_key = os.getenv('LANGFUSE_SECRET_KEY', '')

    print(f"\n配置检查:")
    print(f"  ├─ LANGFUSE_ENABLED: {enabled}")
    print(f"  ├─ LANGFUSE_HOST: {host}")
    print(f"  ├─ LANGFUSE_PUBLIC_KEY: {'已设置' if public_key else '❌ 未设置'}")
    print(f"  └─ LANGFUSE_SECRET_KEY: {'已设置' if secret_key else '❌ 未设置'}")

    if not enabled:
        print("\n❌ Langfuse 未启用")
        print("请在 .env 文件中设置: LANGFUSE_ENABLED=true")
        return False

    if not public_key or not secret_key:
        print("\n❌ API Keys 未配置")
        print("请从 Langfuse UI (http://localhost:3000) 获取 API Keys")
        return False

    # 尝试导入 langfuse
    print("\n库检查:")
    try:
        from langfuse import Langfuse
        print("  ✅ langfuse 包已安装")
    except ImportError:
        print("  ❌ langfuse 包未安装")
        print("     请运行: pip install langfuse>=2.0.0")
        return False

    # 尝试连接
    print("\n连接测试:")
    try:
        client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host
        )

        # Langfuse v3 使用不同的 API
        # 创建一个简单的 generation 来测试连接
        generation = client.generation(
            name="connection_test",
            model="test",
            input="Testing connection from KnowledgeWeaver",
            output="Connection successful!"
        )

        print(f"  ✅ 成功连接到 {host}")
        print(f"  ✅ 测试 generation 已发送")

        # 刷新确保数据发送
        client.flush()
        print(f"  ✅ 数据已同步")

        print(f"\n查看追踪数据:")
        print(f"  👉 访问: {host}/traces")
        print(f"  👉 应该能看到名为 'connection_test' 的追踪")

        return True

    except Exception as e:
        print(f"  ❌ 连接失败: {e}")
        print("\n排查建议:")
        print("  1. 确认 Langfuse 服务运行: docker ps | grep langfuse")
        print("  2. 确认 API Keys 正确（从 UI Settings → API Keys 复制）")
        print(f"  3. 确认可以访问: {host}")
        return False

if __name__ == "__main__":
    success = test_langfuse_connection()

    print("\n" + "=" * 60)
    if success:
        print("🎉 测试成功！Langfuse 已正确配置")
        print("=" * 60)
        print("\n下一步:")
        print("  1. 启动服务: python -m backend.server")
        print("  2. 发送测试请求:")
        print("     curl -X POST http://localhost:9621/qa \\")
        print("       -H 'Content-Type: application/json' \\")
        print("       -d '{\"question\": \"测试问题\", \"mode\": \"auto\"}'")
        print("  3. 查看追踪: http://localhost:3000/traces")
    else:
        print("❌ 测试失败，请按照上述建议排查")
        print("=" * 60)
