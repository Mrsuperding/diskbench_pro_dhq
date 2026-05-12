#!/bin/bash

# IO性能测试管理平台前端部署脚本

echo "🚀 开始部署IO性能测试管理平台前端..."

# 检查Node.js是否安装
if ! command -v node &> /dev/null; then
    echo "❌ Node.js未安装，请先安装Node.js 16+"
    exit 1
fi

# 检查npm是否安装
if ! command -v npm &> /dev/null; then
    echo "❌ npm未安装，请先安装npm"
    exit 1
fi

# 安装依赖
echo "📦 安装项目依赖..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ 依赖安装失败"
    exit 1
fi

# 构建项目
echo "🔨 构建项目..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ 项目构建失败"
    exit 1
fi

# 检查构建结果
if [ ! -d "dist" ]; then
    echo "❌ 构建目录不存在"
    exit 1
fi

echo "✅ 项目构建成功！"
echo "📁 构建文件位于: $(pwd)/dist"
echo ""
echo "🎉 部署完成！"
echo "您可以将 dist 目录中的文件部署到您的Web服务器。"
echo ""
echo "📋 部署选项:"
echo "1. 使用Nginx: 将dist目录配置为Nginx的root目录"
echo "2. 使用Apache: 将dist目录配置为Apache的DocumentRoot"
echo "3. 使用Docker: 运行 ./docker-deploy.sh"
echo "4. 静态托管: 上传到任何支持静态文件托管的平台"
echo ""
echo "🔧 开发环境启动:"
echo "   npm run dev"