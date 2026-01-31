"""
Phoenix Observability
基于 OpenTelemetry 的可观测性

功能：
- Phoenix 客户端管理
- OpenTelemetry 自动追踪
- 零代码修改的 LLM 调用监控
- Session 会话追踪

优势：
1. 基于 OpenTelemetry 开放标准
2. 自动追踪，无需装饰器
3. 内置实验和评估功能
4. 完全开源，本地部署
5. 支持 Session 级别的追踪
"""

import os
import uuid
from typing import Optional, Dict, Any
from contextvars import ContextVar
from dotenv import load_dotenv

load_dotenv()

# 使用 ContextVar 存储当前 session
_current_session: ContextVar[Optional[str]] = ContextVar('current_session', default=None)
_session_metadata: ContextVar[Optional[Dict[str, Any]]] = ContextVar('session_metadata', default=None)


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

                # 注册 OpenTelemetry（官方推荐方式）
                # auto_instrument=True 会自动检测并注入所有已安装的 Instrumentor
                self.tracer_provider = register(
                    project_name=project_name,
                    endpoint=endpoint,
                    auto_instrument=True,  # 🔥 官方推荐：自动注入
                    batch=True  # 生产环境：批量发送，提升性能
                )

                print(f"✅ Phoenix 已启用: {endpoint}")
                print(f"   访问 Phoenix UI: http://localhost:6006")
                print(f"   🔥 自动追踪已启用 (auto_instrument=True)")
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



    def start_session(
        self,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        开始一个新的追踪会话

        Args:
            session_id: 会话ID，如果不提供则自动生成
            metadata: 会话元数据（用户信息、请求来源等）

        Returns:
            会话ID
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        # 设置当前会话
        _current_session.set(session_id)
        _session_metadata.set(metadata or {})

        return session_id

    def get_current_session(self) -> Optional[str]:
        """获取当前会话ID"""
        return _current_session.get()

    def get_session_metadata(self) -> Dict[str, Any]:
        """获取当前会话元数据"""
        return _session_metadata.get() or {}

    def end_session(self):
        """结束当前会话"""
        _current_session.set(None)
        _session_metadata.set(None)

    def add_session_attributes(self, span) -> None:
        """
        为 span 添加 session 属性

        Args:
            span: OpenTelemetry span 对象
        """
        session_id = self.get_current_session()
        if session_id and span:
            span.set_attribute("session.id", session_id)

            # 添加会话元数据
            metadata = self.get_session_metadata()
            for key, value in metadata.items():
                span.set_attribute(f"session.{key}", str(value))


# 全局单例
_phoenix_tracer: Optional[PhoenixTracer] = None


def get_phoenix_tracer() -> PhoenixTracer:
    """获取 Phoenix 追踪器单例"""
    global _phoenix_tracer
    if _phoenix_tracer is None:
        _phoenix_tracer = PhoenixTracer()
    return _phoenix_tracer


# Session 管理辅助函数
def start_session(
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """开始新会话"""
    tracer = get_phoenix_tracer()
    return tracer.start_session(session_id, metadata)


def get_current_session() -> Optional[str]:
    """获取当前会话ID"""
    tracer = get_phoenix_tracer()
    return tracer.get_current_session()


def end_session():
    """结束当前会话"""
    tracer = get_phoenix_tracer()
    tracer.end_session()
