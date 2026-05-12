#!/bin/bash

# IO性能测试管理平台启动脚本

echo "=================================="
echo "IO性能测试管理平台启动脚本"
echo "=================================="

# 检查Python环境
echo "检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3 未安装"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python版本: $PYTHON_VERSION"

# 检查MySQL连接
echo "检查MySQL连接..."
if ! command -v mysql &> /dev/null; then
    echo "警告: MySQL客户端未安装，请确保数据库已配置"
else
    echo "MySQL客户端已安装"
fi

# 安装后端依赖
echo "安装后端依赖..."
cd backend
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "错误: 依赖安装失败"
        exit 1
    fi
else
    echo "错误: requirements.txt 文件不存在"
    exit 1
fi

# 检查数据库配置
echo "检查数据库配置..."
if [ ! -f ".env" ]; then
    echo "创建默认配置文件..."
    cat > .env << EOF
# 数据库配置
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/io_test_platform

# 安全配置
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS配置
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:3000", "http://127.0.0.1:8080"]

# Redis配置
REDIS_URL=redis://localhost:6379

# 监控配置
MONITOR_INTERVAL=5
LOG_RETENTION_DAYS=30

# 任务配置
MAX_CONCURRENT_TASKS=10
TASK_TIMEOUT=3600
EOF
    echo "配置文件已创建，请根据实际情况修改 .env 文件"
fi

# 启动后端服务
echo "启动后端服务..."
echo "后端服务将在 http://localhost:8000 启动"
echo "API文档: http://localhost:8000/docs"
echo ""
echo "默认账号:"
echo "  管理员: admin / admin123"
echo "  普通用户: demo / demo123"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=================================="

python main.py