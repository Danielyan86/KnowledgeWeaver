"""
Progress Tracker
进度追踪模块
"""

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


class ProgressTracker:
    """文档处理进度追踪器"""

    def __init__(self, progress_dir: str = None):
        """
        初始化进度追踪器

        Args:
            progress_dir: 进度文件存储目录
        """
        if progress_dir is None:
            progress_dir = Path(__file__).parent.parent / "data" / "progress"
        self.progress_dir = Path(progress_dir)
        self.progress_dir.mkdir(parents=True, exist_ok=True)

    def _get_progress_file(self, doc_id: str) -> Path:
        """获取进度文件路径"""
        return self.progress_dir / f"{doc_id}.json"

    def start(self, doc_id: str, total_chunks: int, filename: str = None):
        """
        开始追踪进度

        Args:
            doc_id: 文档 ID
            total_chunks: 总块数
            filename: 文件名
        """
        progress = {
            "doc_id": doc_id,
            "filename": filename or doc_id,
            "status": "processing",
            "current": 0,
            "total": total_chunks,
            "stage": "分块完成",
            "progress": 0,
            "started_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "error": None
        }

        progress_file = self._get_progress_file(doc_id)
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

    def update(self, doc_id: str, current: int, stage: str = None):
        """
        更新进度

        Args:
            doc_id: 文档 ID
            current: 当前完成数
            stage: 当前阶段描述
        """
        progress_file = self._get_progress_file(doc_id)

        if not progress_file.exists():
            return

        with open(progress_file, 'r', encoding='utf-8') as f:
            progress = json.load(f)

        progress["current"] = current
        progress["progress"] = int((current / progress["total"]) * 100) if progress["total"] > 0 else 0
        progress["updated_at"] = datetime.now().isoformat()

        if stage:
            progress["stage"] = stage

        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

    def complete(self, doc_id: str, stats: Dict = None):
        """
        标记为完成

        Args:
            doc_id: 文档 ID
            stats: 处理统计信息
        """
        progress_file = self._get_progress_file(doc_id)

        if not progress_file.exists():
            return

        with open(progress_file, 'r', encoding='utf-8') as f:
            progress = json.load(f)

        progress["status"] = "completed"
        progress["progress"] = 100
        progress["stage"] = "处理完成"
        progress["completed_at"] = datetime.now().isoformat()
        progress["updated_at"] = datetime.now().isoformat()

        if stats:
            progress["stats"] = stats

        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

    def fail(self, doc_id: str, error: str):
        """
        标记为失败

        Args:
            doc_id: 文档 ID
            error: 错误信息
        """
        progress_file = self._get_progress_file(doc_id)

        if not progress_file.exists():
            return

        with open(progress_file, 'r', encoding='utf-8') as f:
            progress = json.load(f)

        progress["status"] = "failed"
        progress["stage"] = "处理失败"
        progress["error"] = error
        progress["updated_at"] = datetime.now().isoformat()

        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

    def get(self, doc_id: str) -> Optional[Dict]:
        """
        获取进度信息

        Args:
            doc_id: 文档 ID

        Returns:
            进度信息，如果不存在返回 None
        """
        progress_file = self._get_progress_file(doc_id)

        if not progress_file.exists():
            return None

        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def cancel(self, doc_id: str):
        """
        标记为已取消

        Args:
            doc_id: 文档 ID
        """
        progress_file = self._get_progress_file(doc_id)

        if not progress_file.exists():
            return

        with open(progress_file, 'r', encoding='utf-8') as f:
            progress = json.load(f)

        progress["status"] = "cancelled"
        progress["stage"] = "已取消"
        progress["updated_at"] = datetime.now().isoformat()
        progress["cancelled_at"] = datetime.now().isoformat()

        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

    def is_cancelled(self, doc_id: str) -> bool:
        """
        检查文档是否被取消

        Args:
            doc_id: 文档 ID

        Returns:
            是否已取消
        """
        progress = self.get(doc_id)
        if progress:
            return progress.get("status") == "cancelled"
        return False

    def delete(self, doc_id: str):
        """
        删除进度文件

        Args:
            doc_id: 文档 ID
        """
        progress_file = self._get_progress_file(doc_id)
        if progress_file.exists():
            progress_file.unlink()


# 单例实例
_tracker_instance = None


def get_progress_tracker() -> ProgressTracker:
    """获取进度追踪器实例（单例）"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = ProgressTracker()
    return _tracker_instance
