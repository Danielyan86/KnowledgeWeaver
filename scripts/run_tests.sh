#!/bin/bash
# Test Runner Script
# 测试运行脚本

set -e

echo "================================"
echo "KnowledgeWeaver Test Suite"
echo "================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查是否安装了 pytest
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}错误: pytest 未安装${NC}"
    echo "请运行: pip install -r requirements.txt"
    exit 1
fi

# 解析参数
TEST_TYPE=${1:-all}
COVERAGE=${2:-no}

case $TEST_TYPE in
    unit)
        echo -e "${YELLOW}运行单元测试...${NC}"
        if [ "$COVERAGE" == "coverage" ]; then
            pytest -m unit --cov=backend --cov-report=html --cov-report=term
        else
            pytest -m unit -v
        fi
        ;;
    integration)
        echo -e "${YELLOW}运行集成测试...${NC}"
        pytest -m integration -v
        ;;
    fast)
        echo -e "${YELLOW}运行快速测试（排除慢速测试）...${NC}"
        pytest -m "not slow" -v
        ;;
    coverage)
        echo -e "${YELLOW}运行全部测试并生成覆盖率报告...${NC}"
        pytest --cov=backend --cov-report=html --cov-report=term-missing
        echo ""
        echo -e "${GREEN}覆盖率报告已生成: htmlcov/index.html${NC}"
        ;;
    specific)
        if [ -z "$2" ]; then
            echo -e "${RED}错误: 请指定测试文件${NC}"
            echo "用法: ./run_tests.sh specific tests/test_config.py"
            exit 1
        fi
        echo -e "${YELLOW}运行特定测试: $2${NC}"
        pytest "$2" -v
        ;;
    all)
        echo -e "${YELLOW}运行全部测试...${NC}"
        if [ "$COVERAGE" == "coverage" ]; then
            pytest --cov=backend --cov-report=html --cov-report=term
        else
            pytest -v
        fi
        ;;
    *)
        echo -e "${RED}错误: 未知的测试类型 '$TEST_TYPE'${NC}"
        echo ""
        echo "用法: ./run_tests.sh [test_type] [coverage]"
        echo ""
        echo "测试类型:"
        echo "  all           - 运行全部测试（默认）"
        echo "  unit          - 只运行单元测试"
        echo "  integration   - 只运行集成测试"
        echo "  fast          - 运行快速测试（排除慢速测试）"
        echo "  coverage      - 运行全部测试并生成覆盖率报告"
        echo "  specific FILE - 运行特定测试文件"
        echo ""
        echo "示例:"
        echo "  ./run_tests.sh                              # 运行全部测试"
        echo "  ./run_tests.sh unit                         # 运行单元测试"
        echo "  ./run_tests.sh all coverage                 # 运行全部测试并生成覆盖率"
        echo "  ./run_tests.sh coverage                     # 生成覆盖率报告"
        echo "  ./run_tests.sh specific tests/test_config.py # 运行特定文件"
        exit 1
        ;;
esac

# 检查退出状态
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ 测试通过${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}✗ 测试失败${NC}"
    exit 1
fi
