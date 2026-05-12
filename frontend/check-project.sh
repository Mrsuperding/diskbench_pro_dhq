#!/bin/bash

# 项目文件检查脚本

echo "🔍 检查IO性能测试管理平台前端项目文件..."

# 定义项目文件列表
PROJECT_FILES=(
    "package.json"
    "vite.config.js"
    "tailwind.config.js"
    "index.html"
    "src/main.js"
    "src/App.vue"
    "src/router/index.js"
    "src/api/index.js"
    "src/api/auth.js"
    "src/api/nodes.js"
    "src/api/cases.js"
    "src/api/tasks.js"
    "src/stores/auth.js"
    "src/stores/nodes.js"
    "src/stores/cases.js"
    "src/stores/tasks.js"
    "src/stores/monitor.js"
    "src/views/auth/Login.vue"
    "src/views/auth/Register.vue"
    "src/views/layout/Layout.vue"
    "src/views/dashboard/Index.vue"
    "src/views/nodes/Index.vue"
    "src/views/nodes/Detail.vue"
    "src/views/nodes/components/NodeFormDialog.vue"
    "src/views/nodes/components/BatchTestDialog.vue"
    "src/views/nodes/components/PartitionFormDialog.vue"
    "src/views/cases/Index.vue"
    "src/views/cases/Detail.vue"
    "src/views/cases/components/CaseFormDialog.vue"
    "src/views/cases/components/TemplateDialog.vue"
    "src/views/cases/components/CommandDialog.vue"
    "src/views/tasks/Index.vue"
    "src/views/tasks/Detail.vue"
    "src/views/tasks/components/TaskFormDialog.vue"
    "src/views/tasks/components/TaskLogsDialog.vue"
    "src/views/tasks/components/TaskMetricsDialog.vue"
    "src/views/tasks/components/TaskResultsDialog.vue"
    "src/views/monitor/Index.vue"
    "src/views/users/Index.vue"
    "src/views/profile/Index.vue"
    "src/views/error/404.vue"
    "src/components/TrendIcon.vue"
    "src/style.css"
    "deploy.sh"
    "docker-deploy.sh"
    "README.md"
    "PROJECT_SUMMARY.md"
)

# 检查文件是否存在
MISSING_FILES=()
EXISTING_FILES=()

for file in "${PROJECT_FILES[@]}"; do
    if [ -f "$file" ]; then
        EXISTING_FILES+=("$file")
    else
        MISSING_FILES+=("$file")
    fi
done

# 输出检查结果
echo ""
echo "📊 项目文件检查结果:"
echo "===================="
echo ""
echo "✅ 已创建的文件 (${#EXISTING_FILES[@]}个):"
for file in "${EXISTING_FILES[@]}"; do
    echo "   ✓ $file"
done

echo ""
echo "❌ 缺失的文件 (${#MISSING_FILES[@]}个):"
for file in "${MISSING_FILES[@]}"; do
    echo "   ✗ $file"
done

echo ""
echo "📈 项目完成度: $((${#EXISTING_FILES[@]} * 100 / ${#PROJECT_FILES[@]}))%"

# 检查关键文件
KEY_FILES=(
    "package.json"
    "src/main.js"
    "src/App.vue"
    "src/router/index.js"
    "src/stores/auth.js"
    "src/views/auth/Login.vue"
    "src/views/dashboard/Index.vue"
)

KEY_MISSING=0
for file in "${KEY_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        KEY_MISSING=$((KEY_MISSING + 1))
    fi
done

echo ""
echo "🔑 关键文件状态:"
if [ $KEY_MISSING -eq 0 ]; then
    echo "   ✅ 所有关键文件已创建"
else
    echo "   ⚠️  有 $KEY_MISSING 个关键文件缺失"
fi

# 总体评估
echo ""
echo "🎯 项目状态评估:"
echo "================"

if [ ${#MISSING_FILES[@]} -eq 0 ]; then
    echo "🎉 项目文件创建完成！"
    echo "   所有文件都已成功创建，项目可以正常运行。"
elif [ ${#MISSING_FILES[@]} -lt 5 ]; then
    echo "✅ 项目基本完整！"
    echo "   大部分文件已创建，少量文件缺失不影响主要功能。"
elif [ ${#MISSING_FILES[@]} -lt 15 ]; then
    echo "⚠️  项目部分完成！"
    echo "   核心功能已实现，但还有部分功能需要完善。"
else
    echo "❌ 项目创建不完整！"
    echo "   还有较多文件缺失，建议检查创建过程。"
fi

echo ""
echo "🚀 下一步操作:"
echo "============="
echo "1. 安装依赖: npm install"
echo "2. 启动开发环境: npm run dev"
echo "3. 构建生产版本: npm run build"
echo "4. 部署项目: ./deploy.sh"
echo ""
echo "📚 项目文档:"
echo "   - 项目说明: README.md"
echo "   - 项目总结: PROJECT_SUMMARY.md"
echo ""
echo "✨ 项目创建完成！"