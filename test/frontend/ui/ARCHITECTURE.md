# DiskBench Pro UI 测试框架架构文档

## 1. 目录结构概览

```
test/frontend/ui/
├── conftest.py                    # 主配置文件（根级）
├── pytest.ini                     # Pytest 配置
├── requirements.txt                # 依赖清单
├── Dockerfile                      # CI 容器化配置
│
├── page_objects/                   # 页面对象模型 (POM)
│   ├── __init__.py
│   ├── base/                       # 基础组件
│   │   ├── base_page.py           # BasePage + AutoWait
│   │   └── component.py            # 通用组件封装
│   ├── auth/
│   │   └── login_page.py          # 登录页面对象
│   ├── dashboard/
│   │   └── dashboard_page.py       # 概览页面对象
│   ├── nodes/
│   │   └── nodes_list_page.py     # 节点列表页面对象
│   ├── cases/
│   │   └── cases_list_page.py     # 用例列表页面对象
│   ├── tasks/
│   │   └── tasks_list_page.py     # 任务列表页面对象
│   └── schedules/
│       └── schedules_list_page.py  # 定时调度页面对象
│
├── fixtures/                       # Pytest Fixtures
│   ├── __init__.py
│   └── conftest.py                # Fixture 扩展配置
│
├── config/                         # 多环境配置
│   ├── __init__.py
│   ├── settings.py                # ConfigLoader
│   └── environments/
│       ├── dev.yaml               # 开发环境
│       └── test.yaml              # 测试环境
│
├── data/                          # 测试数据
│   ├── __init__.py
│   ├── login_credentials.yaml      # 登录凭证
│   └── nodes/
│       └── valid_nodes.yaml       # 节点测试数据
│
├── helpers/                        # 工具函数
│   ├── __init__.py
│   ├── screenshot.py              # 截图辅助工具
│   ├── allure_helper.py          # Allure 报告集成
│   └── wait_strategies.py        # 等待策略工具
│
├── hooks/                         # Pytest Hooks
│   ├── __init__.py
│   └── pytest_hooks.py           # 测试生命周期钩子
│
├── tests/                         # POM 测试用例
│   ├── __init__.py
│   ├── test_login_pom.py        # 登录页 POM 测试
│   ├── test_nodes_pom.py         # 节点页 POM 测试
│   ├── test_dashboard_pom.py     # 概览页 POM 测试
│   ├── test_cases_pom.py         # 用例页 POM 测试
│   ├── test_tasks_pom.py         # 任务页 POM 测试
│   └── test_schedules_pom.py     # 调度页 POM 测试
│
├── *_test.py                      # 旧版测试用例
│   ├── login_test.py
│   ├── nodes_test.py
│   ├── dashboard_test.py
│   ├── cases_test.py
│   ├── schedules_test.py
│   └── tasks_test.py
│
└── test-results/                  # 测试结果
    ├── allure-results/            # Allure 报告数据
    ├── screenshots/               # 失败截图
    ├── html/                     # HTML 报告
    └── videos/                    # 失败录像
```

---

## 2. 核心模块详解

### 2.1 page_objects/ — 页面对象模型 (POM)

**设计目的**：将页面元素选择器和操作封装在独立的 Page Object 类中，测试用例只调用业务方法，不直接接触 CSS 选择器。

#### base/base_page.py — 核心基础设施

| 类 | 职责 |
|---|---|
| `AutoWait` | 统一等待策略：元素可见、可点击、隐藏、启用、响应返回、网络空闲 |
| `BasePage` | 所有页面对象的基类，提供 `goto()`、`click()`、`fill()` 等通用操作 |

- `for_visible(selecto**AutoWait 关键方法**：
r, timeout)` — 等待元素可见
- `for_clickable(selector, timeout)` — 等待元素可点击（可见且未禁用）
- `for_hidden(selector, timeout)` — 等待元素隐藏
- `for_enabled(selector, timeout)` — 等待元素启用
- `for_response(url_pattern, status_code)` — 等待 API 响应
- `network_idle(timeout)` — 等待网络空闲
- `wait_until(condition)` — 通用条件等待

**BasePage 关键方法**：
```python
def goto(self, path, wait_until="networkidle")  # 导航
def click(self, selector, timeout)               # 点击
def fill(self, selector, value, timeout)         # 填写
def select_option(self, selector, value)         # 下拉选择
def get_text(self, selector, timeout)            # 获取文本
def get_value(self, selector, timeout)           # 获取输入值
def is_visible(selector, timeout) -> bool       # 检查可见性
def wait_for_url(pattern, timeout)               # 等待 URL 跳转
def screenshot(path, full_page)                 # 截图
```

#### auth/login_page.py — 登录页 POM

```python
class LoginPage(BasePage):
    URL = "/login"

    def login(username, password)           # 执行登录
    def login_as_admin()                  # 管理员登录
    def login_as_demo()                   # 演示用户登录
    def is_login_successful(timeout) -> bool  # 检查是否跳转 dashboard
    def get_error_message() -> str        # 获取错误提示
    def wait_for_error_message(timeout) -> bool
```

#### nodes/nodes_list_page.py — 节点列表页 POM

```python
class NodesListPage(BasePage):
    URL = "/nodes"

    # 搜索过滤
    def search(query)                      # 搜索节点
    def reset_search()                     # 重置搜索
    def filter_by_status(status)           # 按状态筛选

    # 表格操作
    def wait_for_table_loaded(timeout)     # 等待表格加载
    def get_table_row_count() -> int       # 获取行数
    def get_node_names() -> List[str]      # 获取所有节点名
    def get_node_status(node_name) -> str  # 获取节点状态

    # CRUD 操作
    def click_add_node()                   # 点击添加
    def create_node(name, host, port, os_type, ssh_user, ssh_password)
    def click_edit_node(node_name)         # 编辑节点
    def click_delete_node(node_name)       # 删除节点
    def confirm_delete()                   # 确认删除
```

#### base/component.py — 通用组件封装

提供可复用的 UI 组件封装：
- `Button` — 按钮封装
- `Input` — 输入框封装
- `Table` — 表格封装
- `Dialog` — 弹窗封装
- `Pagination` — 分页封装
- `Message` — 消息提示封装

---

### 2.2 fixtures/ — Pytest Fixtures

**conftest.py** 是主 fixture 扩展，提供以下功能：

#### 浏览器相关

| Fixture | 作用域 | 描述 |
|---|---|---|
| `browser_context_args` | session | 浏览器上下文参数（viewport、忽略 HTTPS 错误） |
| `page` | function | 浏览器页面，自动在失败时截图 |

#### 存储相关

| Fixture | 描述 |
|---|---|
| `local_storage` | LocalStorage 操作：get/set/remove/clear/get_all |

#### 认证相关

| Fixture | 描述 |
|---|---|
| `authenticated_page` | 已认证页面（管理员），自动登录 admin 账号 |
| `demo_authenticated_page` | 已认证页面（演示用户），自动登录 demo 账号 |
| `unauthenticated_page` | 全新状态的未认证页面 |

#### 监控相关

| Fixture | 描述 |
|---|---|
| `console_errors` | 控制台错误收集（过滤基础设施错误） |
| `console_errors_with_infra` | 控制台错误收集（包含基础设施错误） |
| `api_responses` | API 响应收集 |
| `failure_context` | 失败上下文捕获器，支持手动截图和 HTML 保存 |

#### 配置相关

| Fixture | 描述 |
|---|---|---|
| `config` | 环境配置对象，支持 `--env` 命令行参数切换环境 |

---

### 2.3 config/ — 多环境配置

#### settings.py — ConfigLoader

配置加载器，支持：
- 多环境配置（dev/test/staging/prod）
- YAML 配置文件加载
- 深度合并默认配置与环境配置
- 命令行 `--env` 参数指定环境
- 环境变量 `TEST_ENV` 指定环境

```bash
pytest --env test  # 使用 test 环境配置
TEST_ENV=prod pytest  # 使用 prod 环境配置
```

#### environments/

| 文件 | 用途 |
|---|---|
| `dev.yaml` | 开发环境配置 |
| `test.yaml` | 测试环境配置 |

配置结构：
```yaml
app:
  base_url: "http://localhost:3000"
  api_url: "http://localhost:8000"

users:
  admin:
    username: "admin"
    password: "admin123"
  demo:
    username: "demo"
    password: "demo123"

wait:
  element: 30000
  navigation: 30000
```

---

### 2.4 data/ — 测试数据

#### login_credentials.yaml

登录凭证数据：
```yaml
admin:
  username: "admin"
  password: "admin123"
demo:
  username: "demo"
  password: "demo123"
```

#### nodes/valid_nodes.yaml

有效的节点测试数据：
```yaml
- name: "Test Node 1"
  host: "192.168.1.101"
  port: 22
  os_type: "linux"
  ssh_user: "root"
  ssh_password: "password"
```

---

## 3. 测试执行流程

### 3.1 Fixture 依赖链

```
browser_context (Playwright)
    ↓
page (browser_context.new_page())
    ↓
local_storage (page.evaluate)
console_errors (page.on "console")
api_responses (page.on "response")
    ↓
authenticated_page (page + local_storage)
    ↓
test_case (authenticated_page, console_errors, ...)
```

### 3.2 失败截图流程

```
测试失败
    ↓
pytest_runtest_makereport hook 存储报告到 request.node.rep_call
    ↓
page fixture teardown 检测 rep_call.failed
    ↓
_capture_failure_screenshot(page, request, config)
    ↓
保存截图到 test-results/screenshots/
```

### 3.3 控制台错误过滤

```
console msg (type="error")
    ↓
ConsoleErrorTracker.handle_console
    ↓
检查是否匹配 KNOWN_INFRA_ERRORS
    ↓
是 → 归类到 infra_errors（不导致测试失败）
否 → 归类到 errors（会导致测试失败）
```

---

## 4. 关键技术特性

### 4.1 AutoWait 等待策略

统一超时机制（默认 30 秒），避免硬编码 `time.sleep()`：

```python
# 旧方式（不推荐）
time.sleep(5)
page.click(selector)

# 新方式（推荐）
self.wait.for_clickable(selector, timeout=5000)
```

### 4.2 控制台错误过滤

基础设施错误（如 Socket.IO 断连、favicon.ico 404）不会导致测试失败：

```python
known_infra_errors = [
    "Socket.IO",
    "favicon.ico",
    "Failed to load resource: the server responded with a status of 404",
]
```

### 4.3 多环境配置

通过 `--env` 参数切换不同环境配置：

```bash
pytest --env dev      # 开发环境
pytest --env test     # 测试环境
pytest --env staging  # 预发布环境
```

---

## 5. 测试用例示例

### 5.1 使用 POM 的测试

```python
# tests/test_login_pom.py
from page_objects.auth.login_page import LoginPage

def test_admin_login_success(authenticated_page):
    """测试管理员登录成功"""
    login_page = LoginPage(authenticated_page)
    login_page.goto()
    login_page.login_as_admin()
    assert login_page.is_login_successful()

def test_login_failure_with_invalid_credentials(page, console_errors):
    """测试无效凭证登录失败"""
    login_page = LoginPage(page)
    login_page.goto()
    login_page.login("admin", "wrong_password")

    error_msg = login_page.get_error_message()
    assert "错误" in error_msg or "失败" in error_msg
    assert len(console_errors) == 0  # 无应用错误
```

### 5.2 使用旧版直接选择器的测试

```python
# login_test.py
def test_login_page_elements(page):
    """测试登录页面元素"""
    page.goto("http://localhost:3000/login")
    assert page.is_visible('input[placeholder="请输入用户名"]')
    assert page.is_visible('input[placeholder="请输入密码"]')
    assert page.is_visible('button:has-text("登录")')
```

---

## 6. 运行测试

### 6.1 基础运行

```bash
cd test/frontend/ui
pip install -r requirements.txt
playwright install --with-deps chromium

pytest -v                          # 运行所有测试
pytest -v --env test              # 使用测试环境配置
pytest -v -k "login"              # 只运行包含 login 的测试
```

### 6.2 报告生成

```bash
# Allure 报告
allure serve test-results/allure-results

# HTML 报告（需安装 pytest-html）
pytest --html=test-results/html-report.html --self-contained-html
```

### 6.3 容器化运行

```bash
# 构建镜像
docker build -t diskbench-ui-test .

# 运行测试
docker run --rm diskbench-ui-test
```

---

## 7. 依赖关系图

```
requirements.txt
    ├── pytest>=7.4.0
    ├── pytest-playwright>=0.4.0
    ├── playwright>=1.40.0
    ├── pytest-xdist>=3.5.0          # 并行执行
    ├── pytest-rerunfailures>=13.0   # 失败重试
    ├── allure-pytest>=2.13.0        # Allure 报告
    ├── pyyaml>=6.0                  # YAML 配置
    └── python-dateutil>=2.8.0
```

---

## 8. 模块状态

| 目录/文件 | 状态 | 说明 |
|---|---|---|
| `hooks/` | ✅ 已完成 | pytest_hooks.py - 测试生命周期钩子 |
| `helpers/` | ✅ 已完成 | screenshot.py, allure_helper.py, wait_strategies.py |
| `page_objects/dashboard/` | ✅ 已完成 | dashboard_page.py |
| `page_objects/cases/` | ✅ 已完成 | cases_list_page.py |
| `page_objects/schedules/` | ✅ 已完成 | schedules_list_page.py |
| `page_objects/tasks/` | ✅ 已完成 | tasks_list_page.py |
| `pytest.ini` | ✅ 已完成 | Pytest 配置文件 |
| 测试用例 | ✅ 已完成 | test_dashboard_pom.py, test_cases_pom.py, test_tasks_pom.py, test_schedules_pom.py |

---

## 9. 设计原则

1. **POM 模式** — 选择器封装在 Page Object 中，测试用例不直接接触 CSS 选择器
2. **统一等待** — 使用 AutoWait 代替硬编码 sleep，通过轮询 + 超时检测元素状态
3. **环境隔离** — 通过 `--env` 参数切换不同环境配置
4. **失败截图** — 测试失败自动截图到 `test-results/screenshots/`
5. **错误过滤** — 基础设施错误（Socket.IO、断连、404）不导致测试失败
6. **Fixture 组合** — 提供可复用的认证、存储、监控 Fixture
