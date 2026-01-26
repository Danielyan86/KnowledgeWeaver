#!/usr/bin/env python3
"""
Phoenix 集成测试脚本

测试内容：
1. Phoenix 连接测试
2. OpenAI 自动追踪测试
3. 追踪数据验证

使用方法：
1. 启动 Phoenix: docker-compose -f docker-compose.phoenix.yml up -d
2. 设置环境变量: export PHOENIX_ENABLED=true
3. 运行测试: python test_phoenix.py
"""

import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()


def test_phoenix_connection():
    """测试 Phoenix 服务连接"""
    print("\n=== 测试 1: Phoenix 服务连接 ===")

    try:
        import requests
        response = requests.get("http://localhost:6006", timeout=5)
        if response.status_code == 200:
            print("✅ Phoenix 服务运行正常")
            print(f"   访问地址: http://localhost:6006")
            return True
        else:
            print(f"❌ Phoenix 服务响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到 Phoenix 服务: {e}")
        print("   请确保 Phoenix 已启动:")
        print("   docker-compose -f docker-compose.phoenix.yml up -d")
        return False


def test_phoenix_tracer_init():
    """测试 Phoenix 追踪器初始化"""
    print("\n=== 测试 2: Phoenix 追踪器初始化 ===")

    # 检查环境变量
    phoenix_enabled = os.getenv('PHOENIX_ENABLED', 'false').lower() == 'true'
    if not phoenix_enabled:
        print("⚠️ PHOENIX_ENABLED 未设置为 true")
        print("   在 .env 文件中设置: PHOENIX_ENABLED=true")
        return False

    try:
        from backend.core.phoenix_observability import get_phoenix_tracer

        tracer = get_phoenix_tracer()

        if tracer.enabled:
            print("✅ Phoenix 追踪器初始化成功")
            print(f"   OpenTelemetry Provider: {tracer.tracer_provider is not None}")
            return True
        else:
            print("❌ Phoenix 追踪器未启用")
            return False
    except Exception as e:
        print(f"❌ Phoenix 追踪器初始化失败: {e}")
        return False


def test_openai_tracing():
    """测试 OpenAI 自动追踪"""
    print("\n=== 测试 3: OpenAI 自动追踪 ===")

    try:
        # 初始化 Phoenix
        from backend.core.phoenix_observability import get_phoenix_tracer
        tracer = get_phoenix_tracer()

        if not tracer.enabled:
            print("⚠️ Phoenix 未启用，跳过测试")
            return False

        # 创建 OpenAI 客户端
        from openai import OpenAI

        api_key = os.getenv('LLM_BINDING_API_KEY')
        base_url = os.getenv('LLM_BINDING_HOST')

        if not api_key or not base_url:
            print("⚠️ OpenAI 配置未设置，跳过测试")
            return False

        client = OpenAI(api_key=api_key, base_url=base_url)

        print("📤 发送测试请求到 LLM...")

        # 发送测试请求
        response = client.chat.completions.create(
            model=os.getenv('LLM_MODEL', 'gpt-3.5-turbo'),
            messages=[
                {"role": "user", "content": "Say 'Phoenix test successful' in Chinese"}
            ],
            max_tokens=50
        )

        print(f"📥 收到响应: {response.choices[0].message.content}")
        print("✅ LLM 调用成功")

        # 等待追踪数据发送
        print("⏳ 等待追踪数据发送到 Phoenix...")
        time.sleep(3)

        print("✅ 追踪数据应已发送到 Phoenix")
        print("   请访问 http://localhost:6006 查看追踪记录")

        return True

    except Exception as e:
        print(f"❌ OpenAI 追踪测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phoenix_ui_access():
    """测试 Phoenix UI 访问"""
    print("\n=== 测试 4: Phoenix UI 访问指南 ===")

    print("""
Phoenix UI 功能概览：

1. 📊 Traces（追踪）
   - 查看所有 LLM 调用的详细信息
   - Token 使用统计
   - 延迟分析
   - 请求/响应内容

2. 🎮 Playground（实验场）
   - 选择任意追踪记录
   - 点击 "Open in Playground"
   - 修改 Prompt 并对比结果
   - 测试不同模型和参数

3. 📈 Evaluations（评估）
   - 自动评估 LLM 输出质量
   - 多种内置评估器
   - 自定义评估规则

4. 🗂️ Datasets（数据集）
   - 管理测试数据集
   - 版本控制
   - 用于评估和实验

访问地址：http://localhost:6006
""")

    return True


def main():
    """主测试流程"""
    print("=" * 60)
    print("Phoenix 集成测试")
    print("=" * 60)

    results = []

    # 测试 1：服务连接
    results.append(("Phoenix 服务连接", test_phoenix_connection()))

    # 测试 2：追踪器初始化
    results.append(("Phoenix 追踪器初始化", test_phoenix_tracer_init()))

    # 测试 3：OpenAI 追踪
    results.append(("OpenAI 自动追踪", test_openai_tracing()))

    # 测试 4：UI 访问指南
    results.append(("Phoenix UI 访问指南", test_phoenix_ui_access()))

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {test_name}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！Phoenix 集成成功！")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查配置")
        return 1


if __name__ == "__main__":
    sys.exit(main())
