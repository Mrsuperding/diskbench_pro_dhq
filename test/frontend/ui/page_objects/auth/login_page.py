"""
Login Page - 登录页面对象
=========================
提供登录页面的元素定位器和操作方法

用法：
    from page_objects.auth.login_page import LoginPage

    def test_login(page):
        login_page = LoginPage(page)
        login_page.goto()
        login_page.login_as_admin()
        assert login_page.is_login_successful()
"""
from playwright.sync_api import Page
from page_objects.base.base_page import BasePage


class LoginSelectors:
    """登录页面选择器"""

    # 输入框
    USERNAME_INPUT = 'input[placeholder="请输入用户名"]'
    PASSWORD_INPUT = 'input[placeholder="请输入密码"]'

    # 按钮
    LOGIN_BUTTON = 'button:has-text("登录")'
    DEMO_ADMIN_LINK = 'a:has-text("admin")'  # 演示管理员链接
    DEMO_DEMO_LINK = 'a:has-text("demo")'    # 演示用户链接

    # 消息
    ERROR_MESSAGE = '.el-message--error, [role="alert"]'
    SUCCESS_MESSAGE = '.el-message--success'

    # 其他
    LOGIN_FORM = '.login-form'
    REMEMBER_ME = '.remember-me input'


class LoginPage(BasePage):
    """
    登录页面对象

    URL: /login
    """

    URL = "/login"

    def __init__(self, page: Page, timeout: int = 30000):
        super().__init__(page, timeout)
        self._selectors = LoginSelectors()

    def goto(self, wait_until: str = "networkidle"):
        """导航到登录页"""
        super().goto(self.URL, wait_until)

    def login(self, username: str, password: str):
        """
        执行登录操作

        Args:
            username: 用户名
            password: 密码
        """
        # 等待输入框可见
        self.wait.for_visible(self.selectors.USERNAME_INPUT)
        self.wait.for_visible(self.selectors.PASSWORD_INPUT)

        # 填写凭证
        self.fill(self.selectors.USERNAME_INPUT, username)
        self.fill(self.selectors.PASSWORD_INPUT, password)

        # 点击登录按钮
        self.click(self.selectors.LOGIN_BUTTON)

    def login_as_admin(self):
        """使用管理员账户登录"""
        admin_creds = {
            "username": "admin",
            "password": "admin123"
        }
        self.login(admin_creds["username"], admin_creds["password"])

    def login_as_demo(self):
        """使用演示账户登录"""
        demo_creds = {
            "username": "demo",
            "password": "demo123"
        }
        self.login(demo_creds["username"], demo_creds["password"])

    def fill_demo_credentials(self, user_type: str = "admin"):
        """
        点击演示链接填充凭证

        Args:
            user_type: "admin" 或 "demo"
        """
        selector = self.selectors.DEMO_ADMIN_LINK if user_type == "admin" else self.selectors.DEMO_DEMO_LINK
        self.click(selector)

    def get_error_message(self) -> str:
        """获取错误消息文本"""
        if self.is_visible(self.selectors.ERROR_MESSAGE, timeout=3000):
            return self.get_text(self.selectors.ERROR_MESSAGE)
        return ""

    def get_success_message(self) -> str:
        """获取成功消息文本"""
        if self.is_visible(self.selectors.SUCCESS_MESSAGE, timeout=3000):
            return self.get_text(self.selectors.SUCCESS_MESSAGE)
        return ""

    def is_login_successful(self, timeout: int = 10000) -> bool:
        """
        检查登录是否成功（是否跳转到 dashboard）

        Args:
            timeout: 超时时间（毫秒）

        Returns:
            True if redirected to dashboard, False otherwise
        """
        try:
            self.wait_for_url("**/dashboard", timeout=timeout)
            return True
        except Exception:
            return False

    def is_at_login_page(self) -> bool:
        """检查是否在登录页"""
        return "/login" in self.url

    def is_login_button_enabled(self) -> bool:
        """检查登录按钮是否启用"""
        button = self.page.locator(self.selectors.LOGIN_BUTTON)
        return not button.is_disabled()

    def clear_credentials(self):
        """清空凭证输入框"""
        username_input = self.page.locator(self.selectors.USERNAME_INPUT)
        password_input = self.page.locator(self.selectors.PASSWORD_INPUT)
        username_input.fill("")
        password_input.fill("")

    def submit_with_enter(self, username: str, password: str):
        """
        使用回车键提交登录

        Args:
            username: 用户名
            password: 密码
        """
        self.wait.for_visible(self.selectors.USERNAME_INPUT)
        self.fill(self.selectors.USERNAME_INPUT, username)
        self.fill(self.selectors.PASSWORD_INPUT, password)
        self.press(self.selectors.PASSWORD_INPUT, "Enter")

    def wait_for_error_message(self, timeout: int = 5000) -> bool:
        """等待错误消息出现"""
        try:
            self.wait.for_visible(self.selectors.ERROR_MESSAGE, timeout=timeout)
            return True
        except Exception:
            return False

    def wait_for_success_message(self, timeout: int = 5000) -> bool:
        """等待成功消息出现"""
        try:
            self.wait.for_visible(self.selectors.SUCCESS_MESSAGE, timeout=timeout)
            return True
        except Exception:
            return False