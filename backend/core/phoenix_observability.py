"""
Phoenix Observability
基于 OpenTelemetry 的可观测性

功能：
- Phoenix 客户端管理
- OpenTelemetry 自动追踪
- 零代码修改的 LLM 调用监控

优势：
1. 基于 OpenTelemetry 开放标准
2. 自动追踪，无需装饰器
3. 内置实验和评估功能
4. 完全开源，本地部署
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class PhoenixTracer:
    """
    Phoenix 追踪器（单例）

    特点：
    1. 自动追踪 OpenAI 调用（零代码修改）
    2. 支持 LangChain、LlamaIndex 等框架
    3. 基于 OpenTelemetry，数据可导出到任何系统
    """

    _instance: Optional['PhoenixTracer'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化 Phoenix 追踪器"""
        if hasattr(self, '_initialized'):
            return

        self.enabled = os.getenv('PHOENIX_ENABLED', 'false').lower() == 'true'
        self.tracer_provider = None

        if self.enabled:
            try:
                from phoenix.otel import register

                endpoint = os.getenv(
                    'PHOENIX_COLLECTOR_ENDPOINT',
                    'http://localhost:4317'
                )
                project_name = os.getenv(
                    'PHOENIX_PROJECT_NAME',
                    'knowledge-weaver'
                )

                # 注册 OpenTelemetry
                self.tracer_provider = register(
                    project_name=project_name,
                    endpoint=endpoint
                )

                # 自动追踪 OpenAI
                self._instrument_openai()

                print(f"✅ Phoenix 已启用: {endpoint}")
                print(f"   访问 Phoenix UI: http://localhost:6006")
            except ImportError as e:
                print(f"⚠️ Phoenix 包未安装，追踪已禁用: {e}")
                print("   安装: pip install arize-phoenix arize-phoenix-otel openinference-instrumentation-openai")
                self.enabled = False
                self.tracer_provider = None
            except Exception as e:
                print(f"⚠️ Phoenix 初始化失败: {e}")
                self.enabled = False
                self.tracer_provider = None
        else:
            self.tracer_provider = None
            print("ℹ️ Phoenix 追踪已禁用")

        self._initialized = True

    def _instrument_openai(self):
        """追踪 OpenAI 调用"""
        if not self.enabled:
            return

        try:
            from openinference.instrumentation.openai import OpenAIInstrumentor

            OpenAIInstrumentor().instrument(
                tracer_provider=self.tracer_provider
            )
            print("✅ OpenAI 自动追踪已启用")
        except ImportError as e:
            print(f"⚠️ OpenAI 追踪失败: {e}")
            print("   安装: pip install openinference-instrumentation-openai")

    def instrument_langchain(self):
        """追踪 LangChain（可选）"""
        if not self.enabled:
            return

        try:
            from openinference.instrumentation.langchain import LangChainInstrumentor

            LangChainInstrumentor().instrument(
                tracer_provider=self.tracer_provider
            )
            print("✅ LangChain 追踪已启用")
        except ImportError:
            pass  # LangChain 是可选依赖

    def instrument_llama_index(self):
        """追踪 LlamaIndex（可选）"""
        if not self.enabled:
            return

        try:
            from openinference.instrumentation.llama_index import LlamaIndexInstrumentor

            LlamaIndexInstrumentor().instrument(
                tracer_provider=self.tracer_provider
            )
            print("✅ LlamaIndex 追踪已启用")
        except ImportError:
            pass  # LlamaIndex 是可选依赖


# 全局单例
_phoenix_tracer: Optional[PhoenixTracer] = None


def get_phoenix_tracer() -> PhoenixTracer:
    """获取 Phoenix 追踪器单例"""
    global _phoenix_tracer
    if _phoenix_tracer is None:
        _phoenix_tracer = PhoenixTracer()
    return _phoenix_tracer
