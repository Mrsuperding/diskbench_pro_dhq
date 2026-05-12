"""
BasePage - 页面对象基类，包含统一的等待策略
=============================================
提供：
- AutoWait: 元素等待策略
- BasePage: 页面对象基类

用法：
    from page_objects import BasePage

    class MyPage(BasePage):
        URL = "/my-page"

        def login(self, username, password):
            self.fill(self.selectors.USERNAME, username)
            self.click(self.selectors.LOGIN_BTN)
"""
from typing import Optional, Union, List, Callable
from playwright.sync_api import Page, Locator, TimeoutError as PlaywrightTimeoutError
import logging
import time


class AutoWait:
    """
    统一等待策略类

    提供元素状态等待、网络响应等待、条件等待等
    默认超时 30 秒，可覆盖
    """

    DEFAULT_TIMEOUT = 30000  # 30 seconds
    POLL_INTERVAL = 100     # 100ms

    def __init__(self, page: Page, timeout: int = DEFAULT_TIMEOUT):
        self.page = page
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)

    # ========== 元素状态等待 ==========

    def for_element(self, selector: str, timeout: Optional[int] = None) -> Locator:
        """等待元素存在于 DOM（可能不可见）"""
        t = timeout or self.timeout
        return self.page.locator(selector).first

    def for_visible(self, selector: str, timeout: Optional[int] = None) -> Locator:
        """等待元素可见"""
        t = timeout or self.timeout
        locator = self.page.locator(selector).first
        locator.wait_for(state="visible", timeout=t)
        return locator

    def for_hidden(self, selector: str, timeout: Optional[int] = None) -> Locator:
        """等待元素隐藏或不存在"""
        t = timeout or self.timeout
        locator = self.page.locator(selector).first
        locator.wait_for(state="hidden", timeout=t)
        return locator

    def for_enabled(self, selector: str, timeout: Optional[int] = None) -> Locator:
        """等待元素启用（可交互）"""
        t = timeout or self.timeout
        locator = self.page.locator(selector).first
        locator.wait_for(state="attached", timeout=t)
        # 检查是否禁用
        start_time = time.time()
        while time.time() - start_time < t / 1000:
            if not locator.is_disabled():
                return locator
            time.sleep(0.1)
        raise PlaywrightTimeoutError(f"Element not enabled: {selector}")

    def for_clickable(self, selector: str, timeout: Optional[int] = None) -> Locator:
        """等待元素可点击（可见且启用）"""
        t = timeout or self.timeout
        locator = self.page.locator(selector).first
        locator.wait_for(state="visible", timeout=t)
        # 注意：Playwright wait_for 不支持 "enabled" 状态，我们通过循环检查
        start_time = time.time()
        while time.time() - start_time < t / 1000:
            if not locator.is_disabled():
                return locator
            time.sleep(0.1)
        raise PlaywrightTimeoutError(f"Element not clickable: {selector}")

    # ========== 文本/属性等待 ==========

    def for_text(self, selector: str, text: str, timeout: Optional[int] = None) -> Locator:
        """等待元素包含指定文本"""
        t = timeout or self.timeout
        locator = self.page.locator(selector).first
        start_time = time.time()
        while time.time() - start_time < t / 1000:
            if text in locator.inner_text():
                return locator
            time.sleep(0.1)
        raise PlaywrightTimeoutError(f"Text '{text}' not found in: {selector}")

    def for_attribute(self, selector: str, attribute: str, value: str, timeout: Optional[int] = None) -> Locator:
        """等待元素属性匹配指定值"""
        t = timeout or self.timeout
        locator = self.page.locator(selector).first
        start_time = time.time()
        while time.time() - start_time < t / 1000:
            attr_val = locator.get_attribute(attribute)
            if attr_val and value in attr_val:
                return locator
            time.sleep(0.1)
        raise PlaywrightTimeoutError(f"Attribute {attribute} not containing '{value}' in: {selector}")

    # ========== 网络等待 ==========

    def for_response(self, url_pattern: str, timeout: Optional[int] = None, status_code: Optional[int] = None):
        """
        等待 URL 匹配模式的响应

        Args:
            url_pattern: URL 匹配模式（支持 glob 和 regex）
            timeout: 超时时间
            status_code: 期望的状态码（可选）

        Returns:
            Response 对象
        """
        t = timeout or self.timeout

        def match_response(response):
            import fnmatch
            if fnmatch.fnmatch(response.url, url_pattern):
                if status_code is None or response.status == status_code:
                    return True
            return False

        start_time = time.time()
        while time.time() - start_time < t / 1000:
            for response in self.page._adapter._browser_context._responses:
                # Note: This is a simplified check
                pass

        # 使用 Playwright 内置的 response 等待
        try:
            response = self.page.wait_for_response(
                lambda r: fnmatch.fnmatch(r.url, url_pattern) and (status_code is None or r.status == status_code),
                timeout=t
            )
            return response
        except Exception:
            self.logger.warning(f"Response not found for pattern: {url_pattern}")
            return None

    def network_idle(self, timeout: Optional[int] = None):
        """等待网络空闲"""
        t = timeout or self.timeout
        self.page.wait_for_load_state("networkidle", timeout=t)

    def for_navigation(self, timeout: Optional[int] = None):
        """等待导航完成（networkidle）"""
        self.network_idle(timeout)

    # ========== 条件等待 ==========

    def wait_until(self, condition: Callable[[], bool], timeout: Optional[int] = None, poll_interval: Optional[int] = None) -> bool:
        """等待条件返回 True"""
        t = timeout or self.timeout
        p = poll_interval or self.POLL_INTERVAL

        start = time.time()
        while time.time() - start < t / 1000:
            try:
                if condition():
                    return True
            except Exception:
                pass
            time.sleep(p / 1000)
        return False

    def wait_for_function(self, fn: str, timeout: Optional[int] = None) -> any:
        """等待 JS 函数返回 truthy 值"""
        t = timeout or self.timeout
        return self.page.wait_for_function(fn, timeout=t)

    # ========== 自定义断言 ==========

    def assert_visible(self, selector: str, timeout: Optional[int] = None, message: Optional[str] = None):
        """断言元素可见"""
        t = timeout or self.timeout
        try:
            self.for_visible(selector, t)
        except PlaywrightTimeoutError:
            msg = message or f"Element not visible: {selector}"
            raise AssertionError(msg)

    def assert_hidden(self, selector: str, timeout: Optional[int] = None, message: Optional[str] = None):
        """断言元素隐藏"""
        t = timeout or self.timeout
        try:
            self.for_hidden(selector, t)
        except PlaywrightTimeoutError:
            msg = message or f"Element not hidden: {selector}"
            raise AssertionError(msg)

    def assert_element_count(self, selector: str, expected_count: int, timeout: Optional[int] = None, message: Optional[str] = None):
        """断言元素数量"""
        t = timeout or self.timeout
        self.page.wait_for_selector(selector, state="attached", timeout=t)
        actual = len(self.page.query_selector_all(selector))
        assert actual == expected_count, (message or f"Expected {expected_count} elements, found {actual}")


class BasePage:
    """
    页面对象基类

    提供：
    - 统一的导航方法 goto()
    - 统一的元素操作 click(), fill(), select_option()
    - 内置的 AutoWait 等待策略
    - 日志记录

    使用方式：
        class LoginPage(BasePage):
            URL = "/login"

            def __init__(self, page: Page):
                super().__init__(page)
                self.selectors = LoginSelectors()

            def login(self, username, password):
                self.fill(self.selectors.USERNAME, username)
                self.click(self.selectors.LOGIN_BTN)
    """

    BASE_URL = "http://localhost:3000"

    def __init__(self, page: Page, timeout: int = AutoWait.DEFAULT_TIMEOUT):
        self.page = page
        self.wait = AutoWait(page, timeout)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._selectors = None

    @property
    def selectors(self):
        """子类需要定义自己的 selectors"""
        if self._selectors is None:
            raise NotImplementedError("Subclass must define selectors")
        return self._selectors

    def goto(self, path: str, wait_until: str = "networkidle"):
        """
        导航到页面路径

        Args:
            path: 路径（以 / 开头）或完整 URL
            wait_until: 等待加载状态 (load/domcontentloaded/networkidle)
        """
        if path.startswith("http"):
            url = path
        else:
            url = f"{self.BASE_URL}{path}" if path.startswith("/") else f"{self.BASE_URL}/{path}"

        self.logger.info(f"Navigating to: {url}")
        self.page.goto(url, wait_until=wait_until)

    def click(self, selector: str, timeout: Optional[int] = None):
        """点击元素（自动等待可点击状态）"""
        elem = self.wait.for_clickable(selector, timeout)
        elem.click()
        self.logger.debug(f"Clicked: {selector}")

    def fill(self, selector: str, value: str, timeout: Optional[int] = None):
        """填写输入框（自动等待可见）"""
        elem = self.wait.for_visible(selector, timeout)
        elem.fill(value)
        self.logger.debug(f"Filled {selector} with: {value[:10]}...")

    def select_option(self, selector: str, value: str, timeout: Optional[int] = None):
        """选择下拉选项"""
        elem = self.wait.for_clickable(selector, timeout)
        elem.select_option(value)

    def get_text(self, selector: str, timeout: Optional[int] = None) -> str:
        """获取元素文本"""
        elem = self.wait.for_visible(selector, timeout)
        return elem.inner_text()

    def get_value(self, selector: str, timeout: Optional[int] = None) -> str:
        """获取输入框的值"""
        elem = self.wait.for_visible(selector, timeout)
        return elem.input_value()

    def is_visible(self, selector: str, timeout: int = 5000) -> bool:
        """检查元素是否可见"""
        try:
            self.wait.for_visible(selector, timeout)
            return True
        except PlaywrightTimeoutError:
            return False

    def is_hidden(self, selector: str, timeout: int = 5000) -> bool:
        """检查元素是否隐藏"""
        try:
            self.wait.for_hidden(selector, timeout)
            return True
        except PlaywrightTimeoutError:
            return False

    def wait_for_url(self, pattern: str, timeout: Optional[int] = None):
        """等待 URL 匹配模式"""
        t = timeout or self.wait.timeout
        self.page.wait_for_url(pattern, timeout=t)
        self.logger.debug(f"URL matched: {pattern}")

    def hover(self, selector: str, timeout: Optional[int] = None):
        """悬停在元素上"""
        elem = self.wait.for_visible(selector, timeout)
        elem.hover()

    def press(self, selector: str, key: str, timeout: Optional[int] = None):
        """按下键盘按键"""
        elem = self.wait.for_visible(selector, timeout)
        elem.press(key)

    def scroll_to(self, selector: str, timeout: Optional[int] = None):
        """滚动到元素"""
        elem = self.wait.for_visible(selector, timeout)
        elem.scroll_into_view_if_needed()

    def screenshot(self, path: str, full_page: bool = False):
        """截图"""
        self.page.screenshot(path=path, full_page=full_page)

    @property
    def url(self) -> str:
        """获取当前 URL"""
        return self.page.url

    @property
    def title(self) -> str:
        """获取页面标题"""
        return self.page.title()

    def reload(self, wait_until: str = "networkidle"):
        """刷新页面"""
        self.page.reload(wait_until=wait_until)

    def back(self, wait_until: str = "networkidle"):
        """后退"""
        self.page.go_back(wait_until=wait_until)

    def forward(self, wait_until: str = "networkidle"):
        """前进"""
        self.page.go_forward(wait_until=wait_until)