"""
Test Progress Tracker
测试进度追踪器
"""

import pytest
import json
from pathlib import Path
from backend.management.progress_tracker import ProgressTracker


@pytest.mark.unit
class TestProgressTracker:
    """测试进度追踪器"""

    @pytest.fixture
    def tracker(self, test_data_dir):
        """创建进度追踪器实例"""
        progress_dir = test_data_dir / "progress"
        return ProgressTracker(str(progress_dir))

    def test_init_creates_directory(self, test_data_dir):
        """测试初始化创建目录"""
        progress_dir = test_data_dir / "progress_test"
        tracker = ProgressTracker(str(progress_dir))

        assert progress_dir.exists()
        assert progress_dir.is_dir()

    def test_start_progress(self, tracker):
        """测试开始进度追踪"""
        doc_id = "test_doc"
        total = 100
        filename = "test.txt"

        tracker.start(doc_id, total, filename)

        progress = tracker.get(doc_id)
        assert progress is not None
        assert progress["status"] == "processing"
        assert progress["total"] == total
        assert progress["filename"] == filename
        assert progress["current"] == 0

    def test_update_progress(self, tracker):
        """测试更新进度"""
        doc_id = "test_doc"
        tracker.start(doc_id, 100, "test.txt")

        tracker.update(doc_id, 50, "提取实体")

        progress = tracker.get(doc_id)
        assert progress["current"] == 50
        assert progress["percentage"] == 50.0
        assert progress["stage"] == "提取实体"

    def test_complete_progress(self, tracker):
        """测试完成进度"""
        doc_id = "test_doc"
        tracker.start(doc_id, 100, "test.txt")
        tracker.update(doc_id, 100, "处理完成")

        result = {"nodes": 50, "edges": 80}
        tracker.complete(doc_id, result)

        progress = tracker.get(doc_id)
        assert progress["status"] == "completed"
        assert progress["result"] == result

    def test_fail_progress(self, tracker):
        """测试失败进度"""
        doc_id = "test_doc"
        tracker.start(doc_id, 100, "test.txt")

        error_msg = "处理失败：连接错误"
        tracker.fail(doc_id, error_msg)

        progress = tracker.get(doc_id)
        assert progress["status"] == "failed"
        assert progress["error"] == error_msg

    def test_get_nonexistent_progress(self, tracker):
        """测试获取不存在的进度"""
        progress = tracker.get("nonexistent_doc")
        assert progress is None

    def test_persistence(self, tracker, test_data_dir):
        """测试进度持久化"""
        doc_id = "test_doc"
        tracker.start(doc_id, 100, "test.txt")
        tracker.update(doc_id, 50, "处理中")

        # 创建新的追踪器实例（模拟重启）
        new_tracker = ProgressTracker(str(test_data_dir / "progress"))
        progress = new_tracker.get(doc_id)

        assert progress is not None
        assert progress["current"] == 50

    def test_multiple_documents(self, tracker):
        """测试多个文档的进度追踪"""
        doc_ids = ["doc1", "doc2", "doc3"]

        for i, doc_id in enumerate(doc_ids):
            tracker.start(doc_id, 100, f"{doc_id}.txt")
            tracker.update(doc_id, (i + 1) * 30, f"阶段{i + 1}")

        # 检查每个文档的进度
        for i, doc_id in enumerate(doc_ids):
            progress = tracker.get(doc_id)
            assert progress is not None
            assert progress["current"] == (i + 1) * 30

    def test_percentage_calculation(self, tracker):
        """测试百分比计算"""
        doc_id = "test_doc"
        tracker.start(doc_id, 200, "test.txt")

        test_cases = [
            (0, 0.0),
            (50, 25.0),
            (100, 50.0),
            (200, 100.0)
        ]

        for current, expected_percentage in test_cases:
            tracker.update(doc_id, current, "测试")
            progress = tracker.get(doc_id)
            assert progress["percentage"] == expected_percentage

    def test_edge_cases(self, tracker):
        """测试边界情况"""
        # 零总数
        tracker.start("doc1", 0, "test.txt")
        progress = tracker.get("doc1")
        assert progress["total"] == 0

        # 负数（不应该发生，但测试健壮性）
        tracker.start("doc2", 100, "test.txt")
        tracker.update("doc2", -1, "测试")
        progress = tracker.get("doc2")
        # 应该被处理为有效值
        assert progress["current"] >= 0
