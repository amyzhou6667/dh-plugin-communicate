#!/bin/bash
# 启动 DeepSeek Harness 飞书桥接插件

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Python 版本
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1)
        print_info "Python version: $PYTHON_VERSION"
    else
        print_error "Python3 is not installed"
        exit 1
    fi
}

# 检查依赖
check_dependencies() {
    print_info "Checking dependencies..."
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt --quiet
        print_info "Dependencies installed"
    else
        print_warn "requirements.txt not found, skipping dependency installation"
    fi
}

# 检查配置
check_config() {
    print_info "Checking configuration..."

    # 检查必要的环境变量
    if [ -z "$FEISHU_APP_ID" ]; then
        print_warn "FEISHU_APP_ID is not set"
    fi

    if [ -z "$FEISHU_APP_SECRET" ]; then
        print_warn "FEISHU_APP_SECRET is not set"
    fi

    # 检查配置文件
    if [ -f "config.yaml" ]; then
        print_info "Found config.yaml"
    else
        print_warn "config.yaml not found, using environment variables"
    fi
}

# 启动应用
start_app() {
    print_info "Starting DeepSeek Harness Bridge..."

    # 设置默认端口
    if [ -z "$BRIDGE_PORT" ]; then
        BRIDGE_PORT=8080
    fi

    print_info "Bridge port: $BRIDGE_PORT"

    # 启动应用
    python3 -m src.app
}

# 主函数
main() {
    print_info "=========================================="
    print_info "DeepSeek Harness 飞书桥接插件"
    print_info "=========================================="

    check_python
    check_dependencies
    check_config
    start_app
}

# 运行主函数
main
