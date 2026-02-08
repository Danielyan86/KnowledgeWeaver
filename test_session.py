#!/usr/bin/env python
"""
测试 Phoenix Session 追踪功能
"""

import requests
import json

# API 地址
API_URL = "http://localhost:9621"

def test_session_tracking():
    """测试 Session 追踪"""

    print("=" * 70)
    print("Phoenix Session 追踪测试")
    print("=" * 70)
    print()

    # 测试 1: 自动生成 session_id
    print("测试 1: 自动生成 Session ID")
    print("-" * 70)

    response = requests.post(
        f"{API_URL}/qa",
        json={"question": "什么是定投？", "mode": "auto"}
    )

    if response.status_code == 200:
        session_id = response.headers.get("X-Session-ID")
        print(f"✓ 请求成功")
        print(f"✓ Session ID: {session_id}")
        print(f"✓ 状态码: {response.status_code}")
        print()

        # 测试 2: 使用相同 session_id 发送第二个请求
        if session_id:
            print("测试 2: 使用相同 Session ID 发送第二个请求")
            print("-" * 70)

            response2 = requests.post(
                f"{API_URL}/qa",
                json={"question": "定投有什么好处？", "mode": "auto"},
                headers={"X-Session-ID": session_id}
            )

            session_id2 = response2.headers.get("X-Session-ID")
            print(f"✓ 请求成功")
            print(f"✓ Session ID: {session_id2}")
            print(f"✓ Session 保持一致: {session_id == session_id2}")
            print()
    else:
        print(f"✗ 请求失败: {response.status_code}")
        print(f"  响应: {response.text}")
        return

    # 显示 Phoenix UI 信息
    print("=" * 70)
    print("📊 在 Phoenix UI 中查看追踪信息:")
    print("=" * 70)
    print()
    print(f"1. 打开 Phoenix UI: http://localhost:6006")
    print(f"2. 选择项目: knowledge-weaver")
    print(f"3. 进入 Traces 页面")
    print(f"4. 搜索 Session ID: {session_id}")
    print()
    print("你将看到:")
    print("  • 完整的请求链路追踪")
    print("  • session.id 属性")
    print("  • session.path, session.method 等元数据")
    print("  • 问答引擎的执行过程")
    print("  • LLM 调用详情（如果有）")
    print()

if __name__ == "__main__":
    try:
        test_session_tracking()
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到服务，请确保服务正在运行")
        print("  运行: ./scripts/start.sh")
    except Exception as e:
        print(f"✗ 测试失败: {e}")
