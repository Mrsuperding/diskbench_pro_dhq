"""
Login Tests - 使用 POM 的示例测试
==================================
展示如何使用新的 Page Object Model 编写测试

用法：
    pytest test/frontend/ui/tests/test_login_pom.py -v
"""
import pytest
from playwright.sync_api import Page

from page_objects import LoginPage
from page_objects.auth.login_page import LoginSelectors


class TestLoginPage:
    """登录页面测试"""

    def test_login_page_loads(self, page: Page):
        """TC_UI_LOGIN_001 - 登录页面正确加载"""
        login_page = LoginPage(page)
        login_page.goto()

        # 验证页面元素
        assert login_page.is_at_login_page()
        assert login_page.is_visible(LoginSelectors.USERNAME_INPUT)
        assert login_page.is_visible(LoginSelectors.PASSWORD_INPUT)
        assert login_page.is_visible(LoginSelectors.LOGIN_BUTTON)

    def test_login_with_valid_admin_credentials(self, page: Page):
        """TC_UI_LOGIN_002 - 使用管理员凭证登录成功"""
        login_page = LoginPage(page)
        login_page.goto()

        # 使用 POM 登录
        login_page.login_as_admin()

        # 验证登录成功
        assert login_page.is_login_successful()

    def test_login_with_valid_demo_credentials(self, page: Page):
        """TC_UI_LOGIN_003 - 使用演示账户登录成功"""
        login_page = LoginPage(page)
        login_page.goto()

        login_page.login_as_demo()

        assert login_page.is_login_successful()

    def test_login_with_wrong_password(self, page: Page):
        """TC_UI_LOGIN_004 - 错误密码显示错误消息"""
        login_page = LoginPage(page)
        login_page.goto()

        login_page.login("admin", "wrongpassword")

        # 等待错误消息出现
        assert login_page.wait_for_error_message()

    def test_login_with_empty_username(self, page: Page):
        """TC_UI_LOGIN_005 - 空用户名显示错误消息"""
        login_page = LoginPage(page)
        login_page.goto()

        login_page.login("", "admin123")

        # 应该提示输入用户名
        error_msg = login_page.get_error_message()
        assert error_msg and ("用户名" in error_msg or "请输入" in error_msg)

    def test_login_with_empty_password(self, page: Page):
        """TC_UI_LOGIN_006 - 空密码显示错误消息"""
        login_page = LoginPage(page)
        login_page.goto()

        login_page.login("admin", "")

        error_msg = login_page.get_error_message()
        assert error_msg and ("密码" in error_msg or "请输入" in error_msg)

    def test_fill_demo_credentials_link(self, page: Page):
        """TC_UI_LOGIN_007 - 点击演示链接填充凭证"""
        login_page = LoginPage(page)
        login_page.goto()

        # 点击 admin 演示链接
        login_page.fill_demo_credentials("admin")

        # 验证输入框已填充
        username = page.locator(LoginSelectors.USERNAME_INPUT).input_value()
        password = page.locator(LoginSelectors.PASSWORD_INPUT).input_value()

        assert username == "admin"
        assert password == "admin123"

    def test_press_enter_to_submit(self, page: Page):
        """TC_UI_LOGIN_008 - 按回车键提交登录"""
        login_page = LoginPage(page)
        login_page.goto()

        login_page.submit_with_enter("admin", "admin123")

        assert login_page.is_login_successful()


class TestLoginWithAuthenticatedPage:
    """使用 authenticated_page fixture 的登录测试"""

    def test_authenticated_page_has_valid_token(self, authenticated_page: Page, local_storage):
        """TC_UI_AUTH_001 - 已认证页面有有效 token"""
        token = local_storage.get("token")
        assert token is not None and len(token) > 0

    def test_authenticated_page_can_access_dashboard(self, authenticated_page: Page):
        """TC_UI_AUTH_002 - 已认证页面可以访问 dashboard"""
        authenticated_page.goto("/dashboard")
        assert "/dashboard" in authenticated_page.url

    def test_authenticated_page_can_access_nodes(self, authenticated_page: Page):
        """TC_UI_AUTH_003 - 已认证页面可以访问节点页面"""
        authenticated_page.goto("/nodes")
        assert "/nodes" in authenticated_page.url

    def test_unauthenticated_page_redirects_to_login(self, page: Page, local_storage):
        """TC_UI_AUTH_004 - 未认证页面重定向到登录"""
        local_storage.clear()
        page.goto("/dashboard")
        page.wait_for_url("**/login**", timeout=10000)
        assert "/login" in page.url