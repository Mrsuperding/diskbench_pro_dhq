"""
Pytest Fixtures - 主配置文件
=============================
提供：
- config: 环境配置
- page: 浏览器页面（自动截图 on failure）
- local_storage: LocalStorage 操作
- authenticated_page: 已认证页面
- console_errors: 控制台错误收集
- api_responses: API 响应收集
- failure_context: 失败上下文捕获

用法：
    def test_login(authenticated_page):
        authenticated_page.goto("/dashboard")
"""
import os
import pytest
from pathlib import Path
from typing import List
from playwright.sync_api import Page, BrowserContext
from datetime import datetime

try:
    from config.settings import ConfigLoader
except ImportError:
    ConfigLoader = None


# ============================================================================
# Configuration
# ============================================================================

def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption(
        "--env",
        action="store",
        default=os.environ.get("TEST_ENV", "dev"),
        help="Test environment: dev, test, staging, prod"
    )


@pytest.fixture(scope="session")
def config(request):
    """加载环境配置"""
    env = request.config.getoption("--env")
    if ConfigLoader is None:
        # Return a simple config object if ConfigLoader not available
        class SimpleConfig:
            def __init__(self, env):
                self.env = env
                self.viewport = {"width": 1920, "height": 1080}
                self.screenshot_on_failure = True
                self.screenshot_full_page = True
                self.screenshot_directory = "test-results/screenshots"
                self.known_infra_errors = [
                    "Socket.IO", "xhr poll error", "TransportError", "socket.io-client",
                    "favicon.ico", "favicon.svg",
                    "Failed to load resource: the server responded with a status of 404",
                    "Failed to load resource: the server responded with a status of 401",
                    "Failed to load resource: the server responded with a status of 500",
                    "Failed to load resource: the server responded with a status of 503",
                ]
                self.admin_user = {"username": "admin", "password": "admin123", "role": "admin"}
                self.demo_user = {"username": "demo", "password": "demo123", "role": "user"}
        return SimpleConfig(env)
    return ConfigLoader(env)


# ============================================================================
# Browser Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, config):
    """浏览器上下文参数"""
    viewport = config.viewport
    return {
        **browser_context_args,
        "viewport": viewport,
        "ignore_https_errors": True,
    }


@pytest.fixture
def page(browser_context, request, config):
    """
    创建页面，自动在失败时截图

    使用方式：
        def test_example(page):
            page.goto("/")
    """
    page = browser_context.new_page()

    # 失败时自动截图
    yield page

    # 检查测试是否失败
    rep_result = getattr(request.node, "rep_call", None)
    if rep_result and rep_result.failed and config.screenshot_on_failure:
        _capture_failure_screenshot(page, request, config)

    page.close()


def _capture_failure_screenshot(page: Page, request, config: ConfigLoader):
    """捕获失败截图"""
    screenshot_dir = Path(config.screenshot_directory)
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    test_name = request.node.name
    timestamp = datetime.now().strftime("%H%M%S_%f")
    screenshot_file = screenshot_dir / f"{test_name}_{timestamp}.png"

    try:
        page.screenshot(path=str(screenshot_file), full_page=config.screenshot_full_page)
        print(f"\n[Screenshot] Failure captured: {screenshot_file}")
    except Exception as e:
        print(f"\n[Screenshot] Failed to capture: {e}")


# ============================================================================
# LocalStorage Fixtures
# ============================================================================

@pytest.fixture
def local_storage(page: Page):
    """
    LocalStorage 操作接口

    使用方式：
        local_storage.set("token", "abc123")
        token = local_storage.get("token")
        local_storage.clear()
    """
    class LocalStorage:
        def _safe_evaluate(self, script: str, *args):
            try:
                return page.evaluate(script, *args)
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

        def get_all(self) -> dict:
            """获取所有 localStorage 项"""
            return self._safe_evaluate("() => {{ const items = {{}}; for (let i = 0; i < localStorage.length; i++) {{ const key = localStorage.key(i); items[key] = localStorage.getItem(key); }} return items; }}")

    return LocalStorage()


# ============================================================================
# Authentication Fixtures
# ============================================================================

@pytest.fixture
def authenticated_page(page: Page, local_storage, config):
    """
    创建已认证页面（管理员）

    使用方式：
        def test_dashboard(authenticated_page):
            authenticated_page.goto("/dashboard")
    """
    admin_creds = config.admin_user

    # 确保 clean state
    local_storage.clear()

    # 访问登录页
    page.goto(f"{config.base_url}/login")

    # 填写凭证
    page.wait_for_selector('input[placeholder="请输入用户名"]', timeout=10000)
    page.fill('input[placeholder="请输入用户名"]', admin_creds["username"])
    page.fill('input[placeholder="请输入密码"]', admin_creds["password"])

    # 点击登录
    page.click('button:has-text("登录")')

    # 等待跳转到 dashboard
    page.wait_for_url("**/dashboard", timeout=10000)

    yield page

    # 清理
    local_storage.clear()


@pytest.fixture
def demo_authenticated_page(page: Page, local_storage, config):
    """
    创建已认证页面（demo 用户）
    """
    demo_creds = config.demo_user

    local_storage.clear()
    page.goto(f"{config.base_url}/login")
    page.wait_for_selector('input[placeholder="请输入用户名"]', timeout=10000)
    page.fill('input[placeholder="请输入用户名"]', demo_creds["username"])
    page.fill('input[placeholder="请输入密码"]', demo_creds["password"])
    page.click('button:has-text("登录")')
    page.wait_for_url("**/dashboard", timeout=10000)

    yield page
    local_storage.clear()


@pytest.fixture
def unauthenticated_page(page: Page, local_storage):
    """
    创建未认证页面（全新状态）
    """
    local_storage.clear()
    yield page
    local_storage.clear()


# ============================================================================
# Console/API Monitoring Fixtures
# ============================================================================

class ConsoleErrorTracker:
    """控制台错误跟踪器"""

    def __init__(self, known_infra_errors: List[str] = None):
        self.errors = []           # 应用错误
        self.infra_errors = []     # 基础设施错误
        self.all_errors = []       # 所有错误
        self.known_infra_errors = known_infra_errors or []

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

    def summary(self) -> str:
        lines = []
        if self.errors:
            lines.append(f"应用错误 ({len(self.errors)}):")
            for e in self.errors:
                lines.append(f"  - {e[:100]}")
        if self.infra_errors:
            lines.append(f"基础设施错误 ({len(self.infra_errors)}) - 已过滤:")
            for e in self.infra_errors[:5]:
                lines.append(f"  - {e[:60]}")
        return "\n".join(lines) if lines else "无错误"


@pytest.fixture
def console_errors(page: Page, config):
    """
    控制台错误收集器（过滤基础设施错误）

    使用方式：
        def test_something(console_errors):
            page.goto("/")
            assert len(console_errors) == 0
    """
    tracker = ConsoleErrorTracker(config.known_infra_errors)
    page.on("console", tracker.handle_console)
    yield tracker.errors
    page.remove_listener("console", tracker.handle_console)


@pytest.fixture
def console_errors_with_infra(page: Page, config):
    """
    控制台错误收集器（包含基础设施错误）

    用于生成错误报告

    使用方式：
        def test_report_errors(console_errors_with_infra):
            page.goto("/")
            summary = console_errors_with_infra.summary()
            print(summary)
    """
    tracker = ConsoleErrorTracker(config.known_infra_errors)
    page.on("console", tracker.handle_console)
    yield tracker
    page.remove_listener("console", tracker.handle_console)


@pytest.fixture
def api_responses(page: Page):
    """
    API 响应收集器

    使用方式：
        def test_api(api_responses):
            page.goto("/nodes")
            for resp in api_responses:
                print(f"{resp['url']}: {resp['status']}")
    """
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


# ============================================================================
# Failure Context
# ============================================================================

@pytest.fixture
def failure_context(page: Page, request):
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
            """手动捕获截图"""
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
            """捕获页面 HTML"""
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


# ============================================================================
# Pytest Hooks
# ============================================================================

def pytest_configure(config):
    """配置测试会话"""
    # 创建结果目录
    results_dir = Path("test-results")
    results_dir.mkdir(exist_ok=True)
    (results_dir / "screenshots").mkdir(exist_ok=True)
    (results_dir / "videos").mkdir(exist_ok=True)
    (results_dir / "html").mkdir(exist_ok=True)

    # 注册 markers
    config.addinivalue_line("markers", "ui: UI 测试标记")
    config.addinivalue_line("markers", "api: API 测试标记")
    config.addinivalue_line("markers", "slow: 慢速测试")
    config.addinivalue_line("markers", "critical: 关键路径测试")
    config.addinivalue_line("markers", "smoke: 冒烟测试")
    config.addinivalue_line("markers", "auth: 需要认证的测试")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """在测试报告阶段保存失败信息"""
    outcome = yield
    report = outcome.get_result()

    # 存储报告，供 fixtures 访问
    setattr(item, f"rep_{report.when}", report)


def pytest_sessionstart(session):
    """测试会话开始"""
    session.start_time = datetime.now()
    print("\n" + "=" * 60)
    print("DiskBench Pro UI Test Suite")
    print("=" * 60)


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束"""
    start_time = getattr(session, 'start_time', None)
    duration = datetime.now() - start_time if start_time else None
    total = session.testscollected
    passed = sum(1 for s in session.items if hasattr(s, 'rep_call') and s.rep_call.passed)
    failed = sum(1 for s in session.items if hasattr(s, 'rep_call') and s.rep_call.failed)

    print("\n" + "=" * 60)
    print(f"Test Session Summary")
    print(f"  Duration: {duration}")
    print(f"  Total: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print("=" * 60)