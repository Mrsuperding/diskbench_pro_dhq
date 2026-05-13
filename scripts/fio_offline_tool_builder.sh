#!/bin/bash
# fio_offline_tool_builder.sh
# 在有网络的机器上运行，收集 fio 及其依赖库用于离线节点部署
# 输出到项目根目录的 tools/ 文件夹
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TOOLS_DIR="$PROJECT_ROOT/tools"
TMP_DIR="/tmp/fio_offline_$$"

usage() {
    echo "用法: $0 [OPTIONS]"
    echo ""
    echo "选项:"
    echo "  -f, --fio PATH       指定本地 fio 二进制路径"
    echo "  -h, --help           显示帮助"
    exit 1
}

# 解析参数
FIO_PATH=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--fio) FIO_PATH="$2"; shift 2 ;;
        -h|--help) usage ;;
        *) echo "未知参数: $1"; usage ;;
    esac
done

# 创建输出目录
mkdir -p "$TOOLS_DIR/bin"
mkdir -p "$TOOLS_DIR/lib"

echo "[1/5] 查找或安装 fio..."

# 如果没有指定 fio，尝试找系统 fio 或安装
if [ -z "$FIO_PATH" ]; then
    if command -v fio &> /dev/null; then
        FIO_PATH=$(command -v fio)
        echo "找到系统 fio: $FIO_PATH"
    else
        echo " fio 未安装，尝试安装..."
        if command -v apt-get &> /dev/null; then
            apt-get update && apt-get install -y fio
        elif command -v yum &> /dev/null; then
            yum install -y fio
        elif command -v dnf &> /dev/null; then
            dnf install -y fio
        else
            echo "错误: 无法安装 fio，请手动指定 -f 参数"
            exit 1
        fi
        FIO_PATH=$(command -v fio)
    fi
fi

echo "[2/5] 检查 fio 是否支持 libaio..."
if fio --enghelp 2>&1 | grep -qi libaio; then
    echo " fio 支持 libaio ✓"
else
    echo " 警告: 当前 fio 不支持 libaio，建议重新编译"
fi

echo "[3/5] 收集 fio 依赖库..."

# 复制 fio 二进制
cp "$FIO_PATH" "$TOOLS_DIR/bin/fio"
chmod +x "$TOOLS_DIR/bin/fio"
echo "  复制: $FIO_PATH -> tools/bin/fio"

# 收集 fio 依赖的库
LIBCHAIN=$(ldd "$FIO_PATH" 2>/dev/null | awk '{print $3}' | grep -v 'not' | grep -v '=>')

# 收集关键库（libaio, libpthread, libc 等）
for lib in $LIBCHAIN; do
    if [ -f "$lib" ]; then
        libname=$(basename "$lib")
        cp "$lib" "$TOOLS_DIR/lib/"
        echo "  收集: $lib -> tools/lib/$libname"
    fi
done

# 确保 libaio 存在（如果没有，从系统安装后复制）
if [ ! -f "$TOOLS_DIR/lib/libaio.so.1" ] && [ ! -f "$TOOLS_DIR/lib/libaio.so" ]; then
    echo "[4/5] 收集 libaio..."
    if command -v apt-get &> /dev/null; then
        apt-get install -y libaio-dev libaio1 2>/dev/null || apt-get install -y libaio1 2>/dev/null
    elif command -v yum &> /dev/null; then
        yum install -y libaio 2>/dev/null || yum install -y libaio-devel 2>/dev/null
    elif command -v dnf &> /dev/null; then
        dnf install -y libaio 2>/dev/null || dnf install -y libaio-devel 2>/dev/null
    fi

    for lib in /lib64/libaio* /usr/lib64/libaio* /usr/lib/libaio* /lib/libaio*; do
        if [ -f "$lib" ]; then
            cp "$lib" "$TOOLS_DIR/lib/"
            echo "  收集: $lib"
        fi
    done
fi

echo "[5/5] 完成！"

echo ""
echo "文件已保存到: $TOOLS_DIR/"
echo ""
echo "目录结构:"
ls -la "$TOOLS_DIR/bin/" 2>/dev/null || echo "  bin/ (空)"
ls -la "$TOOLS_DIR/lib/" 2>/dev/null || echo "  lib/ (空)"
echo ""
echo "使用方法:"
echo "  1. 打包: tar -czf fio_offline_tools.tar.gz -C tools bin lib"
echo "  2. 上传: POST /api/nodes/{node_id}/upload-tool-bundle"
echo "  3. 或手动: scp fio_offline_tools.tar.gz root@<node>:/opt/"
echo ""
echo "验证:"
echo "  fio --enghelp 2>&1 | grep libaio"
