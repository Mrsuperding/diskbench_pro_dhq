#!/bin/bash

# IO性能测试平台前端 - 快速启动脚本

echo "🚀 IO性能测试平台前端启动脚本"
echo "================================"

# 检查Node.js版本
echo "📋 检查环境..."
node_version=$(node --version)
if [ $? -ne 0 ]; then
    echo "❌ 错误: Node.js未安装"
    echo "请先安装Node.js 16+版本"
    exit 1
fi

echo "✅ Node.js版本: $node_version"

# 检查npm
npm_version=$(npm --version)
if [ $? -ne 0 ]; then
    echo "❌ 错误: npm未安装"
    exit 1
fi

echo "✅ npm版本: $npm_version"

# 检查package.json
if [ ! -f "package.json" ]; then
    echo "❌ 错误: package.json文件不存在"
    exit 1
fi

# 安装依赖
echo ""
echo "📦 安装项目依赖..."
if [ -d "node_modules" ]; then
    echo "依赖已安装，跳过..."
else
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
    echo "✅ 依赖安装完成"
fi

# 项目检查
echo ""
echo "🔍 项目检查..."
node check-project.js
if [ $? -ne 0 ]; then
    echo "❌ 项目检查失败"
    exit 1
fi

# 启动开发服务器
echo ""
echo "🌟 启动开发服务器..."
echo "应用将在 http://localhost:5173 启动"
echo "按 Ctrl+C 停止服务器"
echo ""

npm run dev

# 如果npm命令被中断，给出提示
if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  开发服务器已停止"
    echo ""
    echo "其他可用命令:"
    echo "  npm run build    - 构建生产版本"
    echo "  npm run preview  - 预览构建结果"
    echo "  npm run deploy   - 部署项目"
    echo ""
fi