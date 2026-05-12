"""
前端 UI 测试配置 (Playwright Python)
=====================================
提供：
- browser_type_launch_args: 浏览器启动参数
- local_storage: LocalStorage 操作
- console_errors: 控制台错误收集
- authenticated_page: 已认证页面
- api_responses: API 响应收集

扩展配置 (fixtures/):
- config: 环境配置
- page: 浏览器页面（自动截图 on failure）
- failure_context: 失败上下文捕获
"""
import os
import sys
import pytest
from pathlib import Path
from datetime import datetime

# 添加 fixtures 目录和父目录到 Python 路径
FIXTURES_DIR = Path(__file__).parent / "fixtures"
UI_DIR = Path(__file__).parent
if str(FIXTURES_DIR) not in sys.path:
    sys.path.insert(0, str(FIXTURES_DIR))
if str(UI_DIR) not in sys.path:
    sys.path.insert(0, str(UI_DIR))


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """浏览器启动参数"""
    return {"headless": True}


def pytest_configure(config):
    """pytest 配置"""
    config.addinivalue_line(
        "markers", "ui: UI 测试标记"
    )
    config.addinivalue_line(
        "markers", "api: API 测试标记"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试"
    )
    config.addinivalue_line(
        "markers", "critical: 关键路径测试"
    )
    config.addinivalue_line(
        "markers", "smoke: 冒烟测试"
    )
    config.addinivalue_line(
        "markers", "auth: 需要认证的测试"
    )

    # 创建结果目录
    results_dir = Path("test-results")
    results_dir.mkdir(exist_ok=True)
    (results_dir / "screenshots").mkdir(exist_ok=True)
    (results_dir / "videos").mkdir(exist_ok=True)
    (results_dir / "html").mkdir(exist_ok=True)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """在测试报告阶段保存失败信息"""
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


class LocalStorage:
    """LocalStorage 操作类"""

    def _safe_evaluate(self, script: str, *args):
        try:
            return self.page.evaluate(script, *args)
        except Exception:
            return None

    def get(self, key: str) -> str:
        return self._safe_evaluate(f"() => localStorage.getItem('{key}')")

    def set(self, key: str, value: str):
        self._safe_evaluate(f"(val) => localStorage.setItem('{key}', val)", value)

    def remove(self, key: str):
        self._safe_evaluate(f"() => localStorage.removeItem('{key}')")

    def clear(self):
        self._safe_evaluate("() => localStorage.clear()")


class ConsoleErrorTracker:
    """控制台错误跟踪器"""

    def __init__(self):
        self.errors = []
        self.infra_errors = []
        self.all_errors = []
        self.known_infra_errors = [
            "Socket.IO",
            "xhr poll error",
            "TransportError",
            "socket.io-client",
            "favicon.ico",
            "favicon.svg",
            "Failed to load resource: the server responded with a status of 404",
            "Failed to load resource: the server responded with a status of 401",
            "Failed to load resource: the server responded with a status of 500",
            "Failed to load resource: the server responded with a status of 503",
        ]

    def is_infrastructure_error(self, text: str) -> bool:
        for known in self.known_infra_errors:
            if known in text:
                return True
        return False

    def handle_console(self, msg):
        if msg.type == "error":
            text = msg.text
            self.all_errors.append(text)
            if self.is_infrastructure_error(text):
                self.infra_errors.append(text)
            else:
                self.errors.append(text)

    def clear(self):
        self.errors.clear()
        self.infra_errors.clear()
        self.all_errors.clear()


@pytest.fixture
def local_storage(page):
    """
    LocalStorage 操作 fixture

    提供对 localStorage 的读写操作，用于测试需要操作 localStorage 的场景，
    例如模拟 token 过期、设置用户状态等

    用法示例:
        local_storage.set("diskbench_token", "expired_token")
        value = local_storage.get("diskbench_token")
        local_storage.clear()
    """
    ls = LocalStorage()
    ls.page = page
    return ls


@pytest.fixture
def console_errors(page):
    """控制台错误收集 fixture"""
    tracker = ConsoleErrorTracker()
    page.on("console", tracker.handle_console)
    yield tracker.errors
    page.remove_listener("console", tracker.handle_console)


@pytest.fixture
def console_errors_with_infra(page):
    """控制台错误收集 fixture（包含基础设施错误）"""
    tracker = ConsoleErrorTracker()
    page.on("console", tracker.handle_console)
    yield tracker
    page.remove_listener("console", tracker.handle_console)


@pytest.fixture
def api_responses(page):
    """API 响应收集 fixture"""
    responses = []

    def handle_response(response):
        if "/api/" in response.url:
            responses.append({
                "url": response.url,
                "status": response.status,
                "status_text": response.status_text,
            })

    page.on("response", handle_response)
    yield responses
    page.remove_listener("response", handle_response)


@pytest.fixture
def authenticated_page(page, local_storage):
    """
    已认证页面 fixture（管理员）

    用法示例:
        def test_dashboard(authenticated_page):
            authenticated_page.goto("/dashboard")
    """
    local_storage.clear()

    page.goto("http://localhost:3000/login")
    page.wait_for_selector('input[placeholder="请输入用户名"]', timeout=10000)
    page.fill('input[placeholder="请输入用户名"]', "admin")
    page.fill('input[placeholder="请输入密码"]', "admin123")
    page.click('button:has-text("登录")')
    page.wait_for_url("**/dashboard", timeout=10000)

    yield page

    local_storage.clear()


@pytest.fixture
def test_data_page(authenticated_page):
    """
    已认证页面 fixture，包含测试数据准备

    在测试前创建必要的测试用例和节点数据
    """
    page = authenticated_page

    # 获取 auth token from localStorage for API requests
    token = page.evaluate("() => localStorage.getItem('token')")

    # 检查并创建测试用例 (需要 auth token)
    try:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        # 获取用例列表
        resp = page.request.get("http://localhost:8000/api/cases/", headers=headers)
        if resp.status == 200:
            cases = resp.json()
            if not cases or len(cases) == 0:
                # 创建测试用例
                page.request.post("http://localhost:8000/api/cases/", json={
                    "case_name": "Test Case for UI",
                    "description": "Auto-created test case for UI testing",
                    "test_type": "sequential_read",
                    "block_size": "4k",
                    "iodepth": 1,
                    "numjobs": 1,
                    "runtime": 60,
                    "filesize": "1G",
                    "is_template": False
                }, headers=headers)
    except Exception as e:
        print(f"Failed to create test case: {e}")

    # 检查并创建测试节点
    try:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        resp = page.request.get("http://localhost:8000/api/nodes/", headers=headers)
        if resp.status == 200:
            nodes = resp.json()
            if not nodes or len(nodes) == 0:
                # 创建测试节点
                page.request.post("http://localhost:8000/api/nodes/", json={
                    "node_name": "Test Node UI",
                    "host": "192.168.1.100",
                    "port": 22,
                    "username": "test",
                    "status": "online"
                }, headers=headers)
    except Exception as e:
        print(f"Failed to create test node: {e}")

    yield page


@pytest.fixture
def failure_context(page, request):
    """
    失败上下文捕获器

    使用方式：
        def test_example(failure_context):
            page.goto("/")
            failure_context.capture_screenshot("before_action")
    """
    class FailureContext:
        def __init__(self):
            self.test_name = request.node.name
            self.screenshots = []
            self.start_time = datetime.now()

        def capture_screenshot(self, name: str = "manual"):
            screenshot_dir = Path("test-results/screenshots")
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%H%M%S_%f")
            screenshot_file = screenshot_dir / f"{self.test_name}_{name}_{timestamp}.png"
            try:
                page.screenshot(path=str(screenshot_file), full_page=True)
                self.screenshots.append(str(screenshot_file))
                return screenshot_file
            except Exception as e:
                print(f"Screenshot failed: {e}")
                return None

        def capture_html(self, name: str = "page"):
            html_dir = Path("test-results/html")
            html_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%H%M%S_%f")
            html_file = html_dir / f"{self.test_name}_{name}_{timestamp}.html"
            try:
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(page.content())
                return html_file
            except Exception as e:
                print(f"HTML capture failed: {e}")
                return None

    return FailureContext()
