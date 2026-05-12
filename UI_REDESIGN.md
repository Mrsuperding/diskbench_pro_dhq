# DiskBench Pro · UI 简化总览

将原项目"深色渐变 + 毛玻璃 + 动态粒子"风格重做为**浅色工作台风格**，保留原有功能，大幅降低视觉噪音，提升信息密度。

## 🎨 设计原则

1. **浅色为主** — 默认浅色主题，长时间工作台使用不累眼；保留 `.dark` 类一键切换
2. **单一主色** — 仅 `#2563eb`（蓝）作为品牌色；状态色克制到 4 种（绿/黄/红/青）
3. **扁平化** — 删除所有毛玻璃、渐变叠层、动态粒子
4. **信息密度优先** — 卡片 `padding: 16px`（旧 24px）、标题 18px（旧 24px）、图标 18px（旧 24px）
5. **克制的组件** — 原子化 `.card / .tag / .data-table / .stat / .page-header` 贯穿全站
6. **向后兼容** — 旧代码大量 `text-white/bg-slate-*` 类通过 style.css 兼容层**自动映射**到新色板

## 🗂️ 文件变动一览（20 个前端文件）

### 核心样式 + 布局（3）

| 文件 | 作用 |
|------|------|
| `src/style.css` | CSS 变量系统 + 原子组件 + 旧类名兼容层 + 浅/暗色切换 |
| `src/layouts/index.vue` | 窄侧边栏（200 → 60px 可折叠）+ 内联 SVG 图标 + 顶栏暗色切换 |
| `src/router/index.js` | 注册新的 6 个页面 |

### 全新页面（6）

| 路径 | 对应后端能力 |
|------|--------------|
| `views/dashboard/index.vue` | 仪表盘 |
| `views/schedules/index.vue` | 定时调度管理 |
| `views/baselines/index.vue` | 性能基准管理 |
| `views/alerts/index.vue` | 告警规则 + 事件（两 Tab） |
| `views/run-batches/index.vue` | 运行批次 + 详情抽屉 |
| `views/audit-logs/index.vue` | 审计日志 + 过滤器 |

### 重做页面（1）

| 文件 | 改动 |
|------|------|
| `views/auth/Login.vue` | **彻底重写**：左右双栏布局（左侧品牌介绍、右侧极简表单）；删除 45 个动态粒子 DOM、网格底纹、渐变背景、动漫风格标题 |

### 精简页面（6）

| 文件 | 改动 |
|------|------|
| `views/tasks/index.vue` | 移除顶部 4 个统计卡、标题栏精简 |
| `views/nodes/Index.vue` | 同上 |
| `views/cases/index.vue` | 同上 |
| `views/tasks/Detail.vue` | 标题栏 + 返回按钮统一、状态卡缩小 |
| `views/nodes/Detail.vue` | 同上 |
| `views/cases/Detail.vue` | 同上 |

### 图表组件样式清理（2）

| 文件 | 改动 |
|------|------|
| `views/tasks/components/TaskMetricsDialog.vue` | 清理 50 处 `bg-slate/text-white` 硬编码类；性能抖动对话框样式自动适配浅色 |
| `views/monitor/Index.vue` | 标题栏精简、间距统一、空间缩紧 |

### 已完成的其他文件（之前轮次）

| 文件 | 改动 |
|------|------|
| `views/monitor/chart.vue` | 修复 `ref` 未导入 + 图表样式 |
| `components/PerformanceChart.vue` | 时间轴规范化 |

## 🎯 视觉对比

| 维度 | 旧 UI | 新 UI |
|------|-------|-------|
| **主色** | 深紫蓝渐变 `#0f172a → #1e293b` + 五种状态色 chip | 单一主色 `#2563eb` + 4 状态色（弱底色） |
| **背景** | 渐变毛玻璃 + 毛玻璃卡片 | 平面浅灰底 `#f5f6f8` + 白卡 |
| **侧边栏** | 深蓝 `#001529` + FontAwesome 字体图标 | 白底窄栏 + 内联 SVG 图标 |
| **登录页** | 45 个动态粒子 + 网格底纹 + "动漫风格" | 双栏：品牌介绍 + 极简表单 |
| **标题** | `text-2xl font-bold`（24px） | `page-title`（18px） |
| **卡片** | `p-6 bg-slate-800/50 backdrop-blur` | `p-4 white 1px border` |
| **统计卡** | 大图标色块 + 数字 + 3 行文字 | 简短 label + 数字 + 底部 tag |
| **状态标签** | 带 border + `/30` 底色 + 深色文字 | 弱底色 + 饱和文字（无 border） |
| **Dialog** | 半透明毛玻璃 | 纯白 + 1px 边框 |
| **动画** | fade-in 0.5s + slideUp + pulse + 粒子漂浮 | 仅保留 fade-in 0.2s |

## 🔑 关键技术决策

### 1. CSS 变量 + `.dark` 类切换

```css
:root {
  --bg: #f5f6f8; --surface: #fff; --text: #1f2328;
  --brand: #2563eb; ...
}
.dark {
  --bg: #0d1117; --surface: #161b22; --text: #e6edf3;
  --brand: #3b82f6; ...
}
```

切换只需要 `document.documentElement.classList.toggle('dark')`，所有组件样式自动重算，**无需重新渲染**。

### 2. 旧类名兼容层

旧页面大量使用 `text-white / bg-slate-700 / border-slate-600/50` 这类 Tailwind 类。直接去改 50+ 个 Vue 文件工作量太大。

我在 `style.css` 里加了**高优先级属性选择器**，把这些旧类映射到新 CSS 变量：

```css
.text-white,
[class*="text-slate-100"],
[class*="text-slate-200"] { color: var(--text) !important; }

[class*="bg-slate-700"],
[class*="bg-slate-800"] { background-color: var(--surface) !important; }
```

效果：**旧页面零改动自动变浅色**，新页面走新原子类。

### 3. Element Plus 统一适配

覆写了 Element Plus 的 `.el-input / .el-select / .el-dialog / .el-table / .el-pagination` 等内部类，统一到 CSS 变量色板。

### 4. 原子化组件类

所有新页面只用这几个类就能拼装：

```
.page-header / .page-title / .page-subtitle     -- 页面标题栏
.card / .card-header / .card-body               -- 卡片容器
.data-table                                     -- 表格
.tag + .tag-success/warning/danger/info/neutral -- 状态标签
.stat / .stat-label / .stat-value               -- 统计数字
.dot + .dot-online/offline/running              -- 状态小圆点
```

## 🚀 集成步骤

1. 把 `diskbench_fixes/frontend/src/` 覆盖到原项目对应目录
2. **不需要**改 `tailwind.config.js`（新样式基于 CSS 变量，不依赖 Tailwind 主题）
3. **不需要**安装新依赖
4. 重启前端开发服务器：`npm run dev`
5. 首次打开会用浅色主题；点击右上角图标切换为深色；选择会持久化到 `localStorage`

## 🎨 视觉样例（结构示意）

### 主布局
```
┌──────┬─────────────────────────────────────────────────┐
│      │ Home › 任务 › #123           🌙   👤 admin      │
│ 🟦   ├─────────────────────────────────────────────────┤
│ DB   │                                                 │
│      │  任务                          [刷新] [新建任务] │
│ 概览 │  共 42 个任务 · 3 运行中 · 5 待执行              │
│ ──── │  ┌──────────────────────────────────────────┐   │
│ 资源 │  │ 节点名  主机     状态   CPU    操作      │   │
│ 节点 │  │ node-1 1.2.3.4 ● 在线  42%   [测试]     │   │
│ 用例 │  │ node-2 1.2.3.5 ● 在线  67%   [测试]     │   │
│ ──── │  └──────────────────────────────────────────┘   │
│ 测试 │                                                 │
│ 任务 │                                                 │
│ 调度 │                                                 │
│ 批次 │                                                 │
│ 基准 │                                                 │
└──────┴─────────────────────────────────────────────────┘
```

### 登录页
```
┌─────────────────────┬─────────────────┐
│                     │                 │
│  🟦 DiskBench Pro   │      登录       │
│                     │                 │
│  磁盘 IO 性能        │  用户名         │
│  测试平台            │  [           ]  │
│                     │                 │
│  ✓ 跨系统兼容        │  密码           │
│  ✓ 基准对比          │  [           ]  │
│  ✓ 定时调度          │                 │
│  ✓ 加密存储          │  □记住我  忘记? │
│                     │                 │
│                     │  [   登录    ]  │
│  v1.2 © 2025        │                 │
│                     │  演示：admin|demo│
└─────────────────────┴─────────────────┘
```

## 📝 还可再优化（非紧急）

- `views/auth/Register.vue` 注册页（结构同登录，可以复用双栏布局）
- `views/tasks/components/TaskFormDialog.vue` 等创建/编辑表单对话框的 scoped style 里仍有 `bg-slate-*` 硬编码
- `views/logs/Index.vue` 日志页（当前还没查看过）
- `views/users/Index.vue` 用户管理页
- `views/profile/Index.vue` 个人设置页

这些都**不影响使用**——style.css 的兼容层会让它们自动显示为浅色，只是视觉细节还可以更一致。
