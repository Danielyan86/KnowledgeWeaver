"""
简单的 Langfuse v2 测试脚本
测试 OpenAI wrapper 是否能正确追踪到 Langfuse Dashboard
"""

import os
import time
from dotenv import load_dotenv
from openai import OpenAI
from langfuse.openai import OpenAI as LangfuseOpenAI
from langfuse import Langfuse

load_dotenv()

# 配置
LANGFUSE_HOST = os.getenv('LANGFUSE_HOST', 'http://localhost:3000')
LANGFUSE_PUBLIC_KEY = os.getenv('LANGFUSE_PUBLIC_KEY')
LANGFUSE_SECRET_KEY = os.getenv('LANGFUSE_SECRET_KEY')

# OpenAI 配置（使用 LLM Binding）
OPENAI_API_BASE = os.getenv('LLM_BINDING_HOST', 'https://space.ai-builders.com/backend/v1')
OPENAI_API_KEY = os.getenv('LLM_BINDING_API_KEY', '')
OPENAI_MODEL = os.getenv('LLM_MODEL', 'deepseek')

print("=" * 60)
print("Langfuse v3 测试")
print("=" * 60)
print(f"Langfuse Host: {LANGFUSE_HOST}")
print(f"Langfuse Public Key: {LANGFUSE_PUBLIC_KEY}")
print(f"OpenAI Base URL: {OPENAI_API_BASE}")
print("=" * 60)

# 创建 Langfuse 包装的 OpenAI 客户端
client = LangfuseOpenAI(
    base_url=OPENAI_API_BASE,
    api_key=OPENAI_API_KEY,
)

print("\n发送测试 LLM 请求...")

# 发送一个简单的测试请求
response = client.chat.completions.create(
    model=OPENAI_MODEL,
    messages=[
        {"role": "user", "content": "这是一个 Langfuse 测试消息。请简短回复：已收到。"}
    ],
    max_tokens=50,
)

print(f"\n✅ LLM 响应: {response.choices[0].message.content}")

# 刷新 Langfuse 客户端，确保数据发送到服务器
print("\n正在刷新 Langfuse 客户端...")
langfuse_client = Langfuse(
    public_key=LANGFUSE_PUBLIC_KEY,
    secret_key=LANGFUSE_SECRET_KEY,
    host=LANGFUSE_HOST
)
langfuse_client.flush()
print("✅ Langfuse 客户端已刷新")

# 等待数据处理
print("等待 5 秒让数据处理...")
time.sleep(5)

print("\n" + "=" * 60)
print("测试完成！")
print("请访问以下 URL 查看 trace:")
print(f"{LANGFUSE_HOST}/project/cmkuhwthh0006124hxwtj6hfe/traces")
print("=" * 60)
