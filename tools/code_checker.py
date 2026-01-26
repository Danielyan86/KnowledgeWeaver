#!/usr/bin/env python3
"""
Code Push Checker - 自动代码推送检查工具

功能：
1. 敏感信息检测（API Key、密码、Token）
2. 代码质量检查（Python lint）
3. 文件大小限制
4. 调试代码检测
5. JSON/YAML 语法验证
6. 自定义规则检查

用法：
    python code_checker.py [--staged | --all | --files FILE...]
    python code_checker.py --install  # 安装 git hooks
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class CheckLevel(Enum):
    """检查级别"""
    ERROR = "error"      # 阻止提交
    WARNING = "warning"  # 警告但不阻止
    INFO = "info"        # 仅提示


@dataclass
class CheckResult:
    """检查结果"""
    passed: bool
    level: CheckLevel
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    rule: str = ""

    def __str__(self):
        location = ""
        if self.file:
            location = f"{self.file}"
            if self.line:
                location += f":{self.line}"
            location += " - "

        icon = "✓" if self.passed else ("✗" if self.level == CheckLevel.ERROR else "⚠")
        return f"[{icon}] {location}{self.message}"


@dataclass
class CheckConfig:
    """检查配置"""
    # 敏感信息检测
    secret_patterns: List[Dict] = field(default_factory=list)

    # 文件大小限制（字节）
    max_file_size: int = 5 * 1024 * 1024  # 5MB

    # 忽略的文件/目录
    ignore_patterns: List[str] = field(default_factory=list)

    # 调试代码模式
    debug_patterns: List[Dict] = field(default_factory=list)

    # 是否运行测试
    run_tests: bool = False
    test_command: str = "pytest"

    # 是否检查代码格式
    check_format: bool = True

    # 文件扩展名配置
    python_extensions: Set[str] = field(default_factory=lambda: {".py"})
    json_extensions: Set[str] = field(default_factory=lambda: {".json"})
    yaml_extensions: Set[str] = field(default_factory=lambda: {".yml", ".yaml"})


class CodeChecker:
    """代码检查器"""

    # 默认敏感信息模式
    DEFAULT_SECRET_PATTERNS = [
        {
            "name": "API Key (Generic)",
            "pattern": r"(?i)(api[_-]?key|apikey)\s*[=:]\s*['\"]?([a-zA-Z0-9_\-]{20,})['\"]?",
            "level": "error"
        },
        {
            "name": "AWS Access Key",
            "pattern": r"AKIA[0-9A-Z]{16}",
            "level": "error"
        },
        {
            "name": "AWS Secret Key",
            "pattern": r"(?i)aws(.{0,20})?['\"][0-9a-zA-Z/+]{40}['\"]",
            "level": "error"
        },
        {
            "name": "Private Key",
            "pattern": r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
            "level": "error"
        },
        {
            "name": "Password in Code",
            "pattern": r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"](?![\s\*\{\}])[^'\"]{4,}['\"]",
            "level": "error"
        },
        {
            "name": "Bearer Token",
            "pattern": r"(?i)bearer\s+[a-zA-Z0-9_\-\.=]{20,}",
            "level": "error"
        },
        {
            "name": "GitHub Token",
            "pattern": r"gh[pousr]_[A-Za-z0-9_]{36,}",
            "level": "error"
        },
        {
            "name": "Slack Token",
            "pattern": r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9-]*",
            "level": "error"
        },
        {
            "name": "Generic Secret",
            "pattern": r"(?i)(secret|token|credential)\s*[=:]\s*['\"](?![\s\*\{\}])[^'\"]{8,}['\"]",
            "level": "warning"
        },
        {
            "name": "IP Address (Private)",
            "pattern": r"\b(?:10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b",
            "level": "info"
        }
    ]

    # 默认调试代码模式
    DEFAULT_DEBUG_PATTERNS = [
        {
            "name": "Print Statement",
            "pattern": r"^\s*print\s*\(",
            "extensions": [".py"],
            "level": "warning"
        },
        {
            "name": "Console Log",
            "pattern": r"console\.(log|debug|info|warn|error)\s*\(",
            "extensions": [".js", ".ts", ".jsx", ".tsx"],
            "level": "warning"
        },
        {
            "name": "Debugger Statement",
            "pattern": r"^\s*(debugger|breakpoint\(\))",
            "extensions": [".py", ".js", ".ts"],
            "level": "error"
        },
        {
            "name": "TODO/FIXME",
            "pattern": r"(?i)#\s*(TODO|FIXME|XXX|HACK)\b",
            "extensions": [".py"],
            "level": "info"
        },
        {
            "name": "IPython Embed",
            "pattern": r"(?:IPython\.embed|from IPython import embed|import IPython)",
            "extensions": [".py"],
            "level": "error"
        },
        {
            "name": "PDB Trace",
            "pattern": r"(?:pdb\.set_trace|import pdb)",
            "extensions": [".py"],
            "level": "error"
        }
    ]

    # 默认忽略模式
    DEFAULT_IGNORE_PATTERNS = [
        ".git",
        "__pycache__",
        "*.pyc",
        ".env.example",
        ".env.template",
        "node_modules",
        "venv",
        ".venv",
        "*.log",
        "*.min.js",
        "*.min.css",
        "dist",
        "build",
        ".pytest_cache",
        ".mypy_cache",
        "*.egg-info"
    ]

    def __init__(self, config: Optional[CheckConfig] = None):
        """初始化检查器"""
        self.config = config or CheckConfig()
        self.results: List[CheckResult] = []
        self.project_root = self._find_project_root()

        # 设置默认值
        if not self.config.secret_patterns:
            self.config.secret_patterns = self.DEFAULT_SECRET_PATTERNS
        if not self.config.debug_patterns:
            self.config.debug_patterns = self.DEFAULT_DEBUG_PATTERNS
        if not self.config.ignore_patterns:
            self.config.ignore_patterns = self.DEFAULT_IGNORE_PATTERNS

    def _find_project_root(self) -> Path:
        """查找项目根目录"""
        current = Path.cwd()
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent
        return Path.cwd()

    def _should_ignore(self, file_path: Path) -> bool:
        """检查文件是否应该忽略"""
        path_str = str(file_path)
        for pattern in self.config.ignore_patterns:
            if pattern.startswith("*"):
                if path_str.endswith(pattern[1:]):
                    return True
            elif pattern in path_str:
                return True
        return False

    def _add_result(self, result: CheckResult):
        """添加检查结果"""
        self.results.append(result)

    def check_secrets(self, file_path: Path) -> List[CheckResult]:
        """检查敏感信息"""
        results = []

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return results

        lines = content.split('\n')

        for pattern_config in self.config.secret_patterns:
            pattern = re.compile(pattern_config["pattern"])
            level = CheckLevel(pattern_config.get("level", "error"))

            for line_num, line in enumerate(lines, 1):
                # 跳过注释行
                stripped = line.strip()
                if stripped.startswith('#') or stripped.startswith('//'):
                    continue

                if pattern.search(line):
                    results.append(CheckResult(
                        passed=False,
                        level=level,
                        message=f"可能的敏感信息: {pattern_config['name']}",
                        file=str(file_path),
                        line=line_num,
                        rule="secret-detection"
                    ))

        return results

    def check_debug_code(self, file_path: Path) -> List[CheckResult]:
        """检查调试代码"""
        results = []
        extension = file_path.suffix

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return results

        lines = content.split('\n')

        for pattern_config in self.config.debug_patterns:
            # 检查文件扩展名
            allowed_extensions = pattern_config.get("extensions", [])
            if allowed_extensions and extension not in allowed_extensions:
                continue

            pattern = re.compile(pattern_config["pattern"])
            level = CheckLevel(pattern_config.get("level", "warning"))

            for line_num, line in enumerate(lines, 1):
                if pattern.search(line):
                    results.append(CheckResult(
                        passed=False,
                        level=level,
                        message=f"调试代码: {pattern_config['name']}",
                        file=str(file_path),
                        line=line_num,
                        rule="debug-code"
                    ))

        return results

    def check_file_size(self, file_path: Path) -> Optional[CheckResult]:
        """检查文件大小"""
        try:
            size = file_path.stat().st_size
            if size > self.config.max_file_size:
                size_mb = size / (1024 * 1024)
                max_mb = self.config.max_file_size / (1024 * 1024)
                return CheckResult(
                    passed=False,
                    level=CheckLevel.ERROR,
                    message=f"文件过大: {size_mb:.2f}MB (限制: {max_mb:.2f}MB)",
                    file=str(file_path),
                    rule="file-size"
                )
        except Exception:
            pass
        return None

    def check_json_syntax(self, file_path: Path) -> Optional[CheckResult]:
        """检查 JSON 语法"""
        if file_path.suffix not in self.config.json_extensions:
            return None

        try:
            content = file_path.read_text(encoding='utf-8')
            json.loads(content)
        except json.JSONDecodeError as e:
            return CheckResult(
                passed=False,
                level=CheckLevel.ERROR,
                message=f"JSON 语法错误: {e.msg}",
                file=str(file_path),
                line=e.lineno,
                rule="json-syntax"
            )
        except Exception:
            pass
        return None

    def check_yaml_syntax(self, file_path: Path) -> Optional[CheckResult]:
        """检查 YAML 语法"""
        if file_path.suffix not in self.config.yaml_extensions:
            return None

        try:
            import yaml
            content = file_path.read_text(encoding='utf-8')
            yaml.safe_load(content)
        except ImportError:
            # PyYAML 未安装，跳过检查
            return None
        except yaml.YAMLError as e:
            line = getattr(e, 'problem_mark', None)
            line_num = line.line + 1 if line else None
            return CheckResult(
                passed=False,
                level=CheckLevel.ERROR,
                message=f"YAML 语法错误: {str(e)[:50]}",
                file=str(file_path),
                line=line_num,
                rule="yaml-syntax"
            )
        except Exception:
            pass
        return None

    def check_python_syntax(self, file_path: Path) -> Optional[CheckResult]:
        """检查 Python 语法"""
        if file_path.suffix not in self.config.python_extensions:
            return None

        try:
            content = file_path.read_text(encoding='utf-8')
            compile(content, str(file_path), 'exec')
        except SyntaxError as e:
            return CheckResult(
                passed=False,
                level=CheckLevel.ERROR,
                message=f"Python 语法错误: {e.msg}",
                file=str(file_path),
                line=e.lineno,
                rule="python-syntax"
            )
        except Exception:
            pass
        return None

    def check_file(self, file_path: Path) -> List[CheckResult]:
        """检查单个文件"""
        results = []

        if self._should_ignore(file_path):
            return results

        if not file_path.is_file():
            return results

        # 文件大小检查
        size_result = self.check_file_size(file_path)
        if size_result:
            results.append(size_result)
            return results  # 文件过大，跳过其他检查

        # 敏感信息检查
        results.extend(self.check_secrets(file_path))

        # 调试代码检查
        results.extend(self.check_debug_code(file_path))

        # 语法检查
        json_result = self.check_json_syntax(file_path)
        if json_result:
            results.append(json_result)

        yaml_result = self.check_yaml_syntax(file_path)
        if yaml_result:
            results.append(yaml_result)

        python_result = self.check_python_syntax(file_path)
        if python_result:
            results.append(python_result)

        return results

    def get_staged_files(self) -> List[Path]:
        """获取 git 暂存区的文件"""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode == 0:
                files = [
                    self.project_root / f.strip()
                    for f in result.stdout.strip().split('\n')
                    if f.strip()
                ]
                return files
        except Exception:
            pass
        return []

    def get_all_files(self) -> List[Path]:
        """获取所有跟踪的文件"""
        try:
            result = subprocess.run(
                ["git", "ls-files"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode == 0:
                files = [
                    self.project_root / f.strip()
                    for f in result.stdout.strip().split('\n')
                    if f.strip()
                ]
                return files
        except Exception:
            pass
        return []

    def run_tests(self) -> CheckResult:
        """运行测试"""
        try:
            result = subprocess.run(
                self.config.test_command.split(),
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode == 0:
                return CheckResult(
                    passed=True,
                    level=CheckLevel.INFO,
                    message="所有测试通过",
                    rule="tests"
                )
            else:
                return CheckResult(
                    passed=False,
                    level=CheckLevel.ERROR,
                    message=f"测试失败:\n{result.stdout}\n{result.stderr}",
                    rule="tests"
                )
        except FileNotFoundError:
            return CheckResult(
                passed=True,
                level=CheckLevel.WARNING,
                message=f"测试命令未找到: {self.config.test_command}",
                rule="tests"
            )

    def check_files(self, files: List[Path]) -> Tuple[bool, List[CheckResult]]:
        """检查多个文件"""
        all_results = []

        for file_path in files:
            results = self.check_file(file_path)
            all_results.extend(results)

        # 运行测试
        if self.config.run_tests:
            test_result = self.run_tests()
            all_results.append(test_result)

        # 判断是否通过
        has_errors = any(
            not r.passed and r.level == CheckLevel.ERROR
            for r in all_results
        )

        return not has_errors, all_results

    def print_results(self, results: List[CheckResult]):
        """打印检查结果"""
        # 按级别分组
        errors = [r for r in results if r.level == CheckLevel.ERROR and not r.passed]
        warnings = [r for r in results if r.level == CheckLevel.WARNING and not r.passed]
        infos = [r for r in results if r.level == CheckLevel.INFO and not r.passed]

        if errors:
            print("\n\033[91m=== 错误 (Errors) ===\033[0m")
            for r in errors:
                print(f"  \033[91m{r}\033[0m")

        if warnings:
            print("\n\033[93m=== 警告 (Warnings) ===\033[0m")
            for r in warnings:
                print(f"  \033[93m{r}\033[0m")

        if infos:
            print("\n\033[94m=== 提示 (Info) ===\033[0m")
            for r in infos:
                print(f"  \033[94m{r}\033[0m")

        # 统计
        print(f"\n\033[1m检查完成:\033[0m {len(errors)} 错误, {len(warnings)} 警告, {len(infos)} 提示")

        if errors:
            print("\n\033[91m✗ 检查未通过，请修复错误后再提交\033[0m")
        else:
            print("\n\033[92m✓ 检查通过\033[0m")


def load_config(config_path: Optional[Path] = None) -> CheckConfig:
    """加载配置文件"""
    if config_path is None:
        # 查找项目根目录的配置文件
        current = Path.cwd()
        while current != current.parent:
            for name in [".codecheck.json", ".codecheck.yaml", "codecheck.json"]:
                config_file = current / name
                if config_file.exists():
                    config_path = config_file
                    break
            if config_path:
                break
            if (current / ".git").exists():
                break
            current = current.parent

    config = CheckConfig()

    if config_path and config_path.exists():
        try:
            content = config_path.read_text(encoding='utf-8')
            if config_path.suffix in ('.yaml', '.yml'):
                import yaml
                data = yaml.safe_load(content)
            else:
                data = json.loads(content)

            if data:
                if 'secret_patterns' in data:
                    config.secret_patterns = data['secret_patterns']
                if 'debug_patterns' in data:
                    config.debug_patterns = data['debug_patterns']
                if 'ignore_patterns' in data:
                    config.ignore_patterns = data['ignore_patterns']
                if 'max_file_size' in data:
                    config.max_file_size = data['max_file_size']
                if 'run_tests' in data:
                    config.run_tests = data['run_tests']
                if 'test_command' in data:
                    config.test_command = data['test_command']
        except Exception as e:
            print(f"警告: 加载配置文件失败: {e}")

    return config


def install_hooks(project_root: Path):
    """安装 git hooks"""
    hooks_dir = project_root / ".git" / "hooks"

    if not hooks_dir.exists():
        print("错误: .git/hooks 目录不存在，请确保在 git 仓库中运行")
        return False

    # Pre-commit hook
    pre_commit = hooks_dir / "pre-commit"
    pre_commit_content = '''#!/bin/bash
# Auto-generated by code_checker.py

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 运行代码检查
if command -v python3 &> /dev/null; then
    PYTHON=python3
else
    PYTHON=python
fi

$PYTHON "$PROJECT_ROOT/tools/code_checker.py" --staged

exit $?
'''

    # Pre-push hook
    pre_push = hooks_dir / "pre-push"
    pre_push_content = '''#!/bin/bash
# Auto-generated by code_checker.py

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 运行代码检查（包括测试）
if command -v python3 &> /dev/null; then
    PYTHON=python3
else
    PYTHON=python
fi

$PYTHON "$PROJECT_ROOT/tools/code_checker.py" --staged --run-tests

exit $?
'''

    try:
        # 写入 pre-commit
        pre_commit.write_text(pre_commit_content)
        pre_commit.chmod(0o755)
        print(f"✓ 已安装 pre-commit hook: {pre_commit}")

        # 写入 pre-push
        pre_push.write_text(pre_push_content)
        pre_push.chmod(0o755)
        print(f"✓ 已安装 pre-push hook: {pre_push}")

        return True
    except Exception as e:
        print(f"错误: 安装 hooks 失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="代码推送检查工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --staged        检查暂存区文件
  %(prog)s --all           检查所有跟踪文件
  %(prog)s --files a.py    检查指定文件
  %(prog)s --install       安装 git hooks
        """
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--staged", action="store_true", help="检查 git 暂存区文件")
    group.add_argument("--all", action="store_true", help="检查所有跟踪文件")
    group.add_argument("--files", nargs="+", type=Path, help="检查指定文件")
    group.add_argument("--install", action="store_true", help="安装 git hooks")

    parser.add_argument("--config", type=Path, help="配置文件路径")
    parser.add_argument("--run-tests", action="store_true", help="运行测试")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")

    args = parser.parse_args()

    # 安装 hooks
    if args.install:
        project_root = Path.cwd()
        while project_root != project_root.parent:
            if (project_root / ".git").exists():
                break
            project_root = project_root.parent

        if install_hooks(project_root):
            print("\n✓ Git hooks 安装完成")
            print("  - pre-commit: 提交前自动检查")
            print("  - pre-push: 推送前自动检查（含测试）")
        return

    # 加载配置
    config = load_config(args.config)
    if args.run_tests:
        config.run_tests = True

    # 创建检查器
    checker = CodeChecker(config)

    # 获取要检查的文件
    if args.files:
        files = [Path(f).resolve() for f in args.files]
    elif args.all:
        files = checker.get_all_files()
    else:  # 默认检查暂存区
        files = checker.get_staged_files()

    if not files:
        print("没有需要检查的文件")
        sys.exit(0)

    if args.verbose:
        print(f"检查 {len(files)} 个文件...")

    # 执行检查
    passed, results = checker.check_files(files)

    # 输出结果
    if results:
        checker.print_results(results)
    else:
        print("\n\033[92m✓ 检查通过，没有发现问题\033[0m")

    # 返回状态码
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
