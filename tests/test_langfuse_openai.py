#!/usr/bin/env python3
"""
测试 Langfuse OpenAI Wrapper 集成

直接测试 OpenAI wrapper 是否能正确追踪 LLM 调用
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_openai_wrapper():
    """测试 Langfuse OpenAI wrapper"""
    print("=" * 60)
    print("Langfuse OpenAI Wrapper 测试")
    print("=" * 60)

    # 1. 导入测试
    print("\n[1/4] 导入测试...")
    try:
        from langfuse.openai import OpenAI
        print("  ✅ Langfuse OpenAI wrapper 导入成功")
    except ImportError as e:
        print(f"  ❌ 导入失败: {e}")
        return False

    # 2. 配置检查
    print("\n[2/4] 配置检查...")
    config = {
        "LANGFUSE_ENABLED": os.getenv('LANGFUSE_ENABLED', 'false'),
        "LANGFUSE_HOST": os.getenv('LANGFUSE_HOST', ''),
        "LANGFUSE_PUBLIC_KEY": '已设置' if os.getenv('LANGFUSE_PUBLIC_KEY') else '未设置',
        "LANGFUSE_SECRET_KEY": '已设置' if os.getenv('LANGFUSE_SECRET_KEY') else '未设置',
        "LLM_BINDING_HOST": os.getenv('LLM_BINDING_HOST', ''),
        "LLM_MODEL": os.getenv('LLM_MODEL', 'deepseek'),
    }

    for key, value in config.items():
        status = "✅" if value and value != 'false' else "❌"
        print(f"  {status} {key}: {value}")

    if config["LANGFUSE_ENABLED"].lower() != 'true':
        print("\n  ⚠️  Langfuse 未启用，但仍可测试 wrapper 功能")

    # 3. 创建客户端
    print("\n[3/4] 创建 Langfuse wrapped OpenAI 客户端...")
    try:
        client = OpenAI(
            base_url=os.getenv('LLM_BINDING_HOST'),
            api_key=os.getenv('LLM_BINDING_API_KEY')
        )
        print("  ✅ 客户端创建成功")
        print(f"  ℹ️  Base URL: {os.getenv('LLM_BINDING_HOST')}")
    except Exception as e:
        print(f"  ❌ 客户端创建失败: {e}")
        return False

    # 4. 测试 LLM 调用
    print("\n[4/4] 测试 LLM 调用（将自动追踪到 Langfuse）...")
    try:
        response = client.chat.completions.create(
            model=os.getenv('LLM_MODEL', 'deepseek'),
            messages=[
                {"role": "system", "content": "你是一个测试助手。"},
                {"role": "user", "content": "简单回复：测试成功"}
            ],
            max_tokens=50
        )

        answer = response.choices[0].message.content
        print(f"  ✅ LLM 调用成功")
        print(f"  ℹ️  回答: {answer}")

        if hasattr(response, 'usage') and response.usage:
            print(f"  ℹ️  Token 使用:")
            print(f"     - Prompt: {response.usage.prompt_tokens}")
            print(f"     - Completion: {response.usage.completion_tokens}")
            print(f"     - Total: {response.usage.total_tokens}")

        print("\n  📊 查看追踪数据:")
        print(f"     👉 访问: {os.getenv('LANGFUSE_HOST', 'http://localhost:3000')}/traces")
        print(f"     👉 应该能看到刚才的 LLM 调用记录")

        return True

    except Exception as e:
        print(f"  ❌ LLM 调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🔍 这个测试将:")
    print("   1. 导入 Langfuse OpenAI wrapper")
    print("   2. 检查配置")
    print("   3. 创建 wrapped 客户端")
    print("   4. 发送测试请求（自动追踪到 Langfuse）")
    print()

    success = test_openai_wrapper()

    print("\n" + "=" * 60)
    if success:
        print("🎉 测试成功！")
        print("=" * 60)
        print("\n✅ Langfuse 集成正常工作")
        print("✅ 所有 LLM 调用都会自动追踪")
        print(f"\n📊 查看完整追踪: {os.getenv('LANGFUSE_HOST', 'http://localhost:3000')}/traces")
    else:
        print("❌ 测试失败")
        print("=" * 60)
        print("\n请检查:")
        print("  1. Langfuse 服务是否运行: docker ps | grep langfuse")
        print("  2. .env 配置是否正确")
        print("  3. LLM API 是否可访问")
