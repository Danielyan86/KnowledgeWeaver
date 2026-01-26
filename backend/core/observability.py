"""
Observability with Langfuse
可观测性配置

功能：
- Langfuse 客户端管理
- LLM 调用追踪（使用装饰器和 wrapper，非入侵式）
- 性能监控

最佳实践：
1. 使用 @observe 装饰器自动追踪函数
2. 使用 OpenAI wrapper 自动追踪 LLM 调用
3. 最小化代码修改
"""

import os
from typing import Optional, Dict, Any, Callable
from functools import wraps
from dotenv import load_dotenv

load_dotenv()


class LangfuseTracer:
    """
    Langfuse 追踪器（单例）

    提供两种集成方式：
    1. @observe 装饰器 - 自动追踪函数
    2. OpenAI wrapper - 自动追踪 LLM 调用
    """

    _instance: Optional['LangfuseTracer'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化 Langfuse 客户端"""
        if hasattr(self, '_initialized'):
            return

        self.enabled = os.getenv('LANGFUSE_ENABLED', 'false').lower() == 'true'
        self.client = None
        self.observe = None

        if self.enabled:
            try:
                from langfuse import Langfuse

                # Langfuse v3 不再有 decorators 模块，observe 装饰器已移除
                # 我们主要使用 OpenAI wrapper，不需要 observe 装饰器

                self.client = Langfuse(
                    public_key=os.getenv('LANGFUSE_PUBLIC_KEY'),
                    secret_key=os.getenv('LANGFUSE_SECRET_KEY'),
                    host=os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')
                )
                self.observe = self._dummy_observe  # v3 不支持，使用空装饰器
                print(f"✅ Langfuse 已启用: {os.getenv('LANGFUSE_HOST', 'cloud')}")
            except ImportError as e:
                print(f"⚠️ langfuse 包未安装，追踪已禁用: {e}")
                self.enabled = False
                self.client = None
                self.observe = self._dummy_observe
            except Exception as e:
                print(f"⚠️ Langfuse 初始化失败: {e}")
                self.enabled = False
                self.client = None
                self.observe = self._dummy_observe
        else:
            self.client = None
            self.observe = self._dummy_observe
            print("ℹ️ Langfuse 追踪已禁用")

        self._initialized = True

    def _dummy_observe(self, func: Optional[Callable] = None, **kwargs):
        """当 Langfuse 未启用时的空装饰器"""
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                return f(*args, **kwargs)
            return wrapper

        if func is None:
            return decorator
        return decorator(func)

    def wrap_openai(self, client):
        """
        包装 OpenAI 客户端，自动追踪所有 LLM 调用

        Args:
            client: OpenAI 客户端实例

        Returns:
            包装后的客户端（如果启用）或原客户端（如果未启用）
        """
        if not self.enabled or not self.client:
            return client

        try:
            from langfuse.openai import OpenAI as LangfuseOpenAI

            # 将现有客户端的配置传递给 Langfuse wrapper
            wrapped_client = LangfuseOpenAI(
                base_url=client.base_url,
                api_key=client.api_key
            )
            print("✅ OpenAI 客户端已包装 Langfuse 追踪")
            return wrapped_client
        except Exception as e:
            print(f"⚠️ OpenAI wrapper 失败: {e}，使用原客户端")
            return client

    def flush(self):
        """刷新缓存，确保数据发送到 Langfuse"""
        if self.enabled and self.client:
            try:
                self.client.flush()
            except Exception as e:
                print(f"⚠️ Langfuse flush 失败: {e}")


# 全局单例
_tracer: Optional[LangfuseTracer] = None


def get_tracer() -> LangfuseTracer:
    """获取 Langfuse 追踪器单例"""
    global _tracer
    if _tracer is None:
        _tracer = LangfuseTracer()
    return _tracer
