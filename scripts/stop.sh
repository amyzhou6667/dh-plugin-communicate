#!/bin/bash
# 停止 DeepSeek Harness 飞书桥接插件

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

# 停止应用
stop_app() {
    print_info "Stopping DeepSeek Harness Bridge..."

    # 查找进程
    PIDS=$(pgrep -f "python3 -m src.app" || true)

    if [ -z "$PIDS" ]; then
        print_warn "No running bridge process found"
        return 0
    fi

    # 停止进程
    for PID in $PIDS; do
        print_info "Stopping process $PID..."
        kill "$PID" 2>/dev/null || true
    done

    # 等待进程停止
    sleep 2

    # 检查进程是否还在运行
    PIDS=$(pgrep -f "python3 -m src.app" || true)
    if [ -z "$PIDS" ]; then
        print_info "Bridge stopped successfully"
    else
        print_warn "Some processes are still running, force killing..."
        for PID in $PIDS; do
            kill -9 "$PID" 2>/dev/null || true
        done
        print_info "Bridge force stopped"
    fi
}

# 主函数
main() {
    print_info "=========================================="
    print_info "Stopping DeepSeek Harness Bridge"
    print_info "=========================================="

    stop_app
}

# 运行主函数
main
