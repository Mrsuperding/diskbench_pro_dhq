# Test Directory Structure

> **注意**: 运行测试前请安装依赖
> ```bash
> pip install pytest pytest-playwright requests
> playwright install chromium
> ```

## 目录说明

```
test/
├── README.md
├── TEST_PLAN.md
├── backend/
│   └── api/                    # 后端 API 测试
│       ├── __init__.py
│       ├── conftest.py         # pytest 配置和 fixtures
│       ├── test_auth.py        # 认证接口测试 (8 用例)
│       ├── test_nodes.py       # 节点管理接口测试 (8 用例)
│       ├── test_cases.py       # 用例管理接口测试 (6 用例)
│       ├── test_tasks.py       # 任务管理接口测试 (8 用例)
│       ├── test_monitor.py     # 监控接口测试 (3 用例)
│       ├── test_schedules.py   # 调度任务接口测试 (5 用例)
│       ├── test_baselines.py   # 性能基准接口测试 (3 用例)
│       ├── test_alerts.py      # 告警管理接口测试 (3 用例)
│       └── test_users.py       # 用户管理接口测试 (4 用例)
│
├── frontend/
│   ├── api/                    # 前端 API 测试 (Python)
│   │   ├── test_auth.py
│   │   ├── test_nodes.py
│   │   ├── test_cases.py
│   │   └── test_tasks.py
│   │
│   └── ui/                     # 前端 UI 测试 (Playwright Python)
│       ├── login.spec.py
│       ├── dashboard.spec.py
│       ├── nodes.spec.py
│       ├── cases.spec.py
│       ├── tasks.spec.py
│       └── schedules.spec.py
│
└── results/                    # 测试结果收集目录
```

## 运行方式

### 后端测试
```bash
cd backend
pytest ../test/backend/api/ -v --html=../test/results/backend_api_report.html --self-contained-html
```

### 前端 API 测试
```bash
cd D:\delvelop_project\ai_project\diskbench_pro
pytest test/frontend/api/ -v --html=test/results/frontend_api_report.html
```

### 前端 UI 测试 (Playwright Python)
```bash
cd D:\delvelop_project\ai_project\diskbench_pro
pytest test/frontend/ui/ -v --html=test/results/frontend_ui_report.html --self-contained-html
```

## 测试结果

每轮测试的结果文件存放在 `test/results/` 目录下：
- `backend_api_report.html` - 后端 API 测试报告
- `frontend_ui_report.html` - 前端 UI 测试报告
- `*.json` - 原始测试结果数据
