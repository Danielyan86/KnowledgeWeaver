#!/usr/bin/env python3
"""Phoenix 快速测试"""
import os
import sys

# 设置环境变量（如果尚未设置）
os.environ.setdefault('PHOENIX_ENABLED', 'true')
os.environ.setdefault('PHOENIX_COLLECTOR_ENDPOINT', 'http://localhost:4317')
os.environ.setdefault('PHOENIX_PROJECT_NAME', 'knowledge-weaver')

print("=" * 60)
print("Phoenix 快速集成测试")
print("=" * 60)

# 测试 1: 导入模块
print("\n[测试 1] 导入 Phoenix 模块...")
try:
    from backend.core.phoenix_observability import get_phoenix_tracer
    print("✅ 模块导入成功")
except Exception as e:
    print(f"❌ 模块导入失败: {e}")
    sys.exit(1)

# 测试 2: 初始化追踪器
print("\n[测试 2] 初始化 Phoenix 追踪器...")
try:
    tracer = get_phoenix_tracer()
    if tracer.enabled:
        print("✅ Phoenix 追踪器已启用")
        print(f"   OpenTelemetry Provider: {tracer.tracer_provider is not None}")
    else:
        print("⚠️ Phoenix 追踪器未启用")
        print("   请检查环境变量 PHOENIX_ENABLED=true")
except Exception as e:
    print(f"❌ 初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试 3: 测试 LLM 调用追踪
print("\n[测试 3] 测试 OpenAI 自动追踪...")
try:
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('LLM_BINDING_API_KEY')
    base_url = os.getenv('LLM_BINDING_HOST')
    model = os.getenv('LLM_MODEL', 'gpt-3.5-turbo')
    
    if not api_key or not base_url:
        print("⚠️ OpenAI 配置未设置，跳过 LLM 测试")
    else:
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        print("   发送测试请求...")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say 'Phoenix integration successful' in Chinese"}],
            max_tokens=50
        )
        
        print(f"   响应: {response.choices[0].message.content}")
        print("✅ LLM 调用成功，追踪数据已发送到 Phoenix")
        print("   访问 http://localhost:6006 查看追踪记录")
        
except Exception as e:
    print(f"⚠️ LLM 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("🎉 Phoenix 集成测试完成！")
print("=" * 60)
print("\n下一步:")
print("1. 访问 Phoenix UI: http://localhost:6006")
print("2. 查看追踪数据（Traces 标签）")
print("3. 在 Playground 中优化 Prompt")
print("\n")
