"""
前端 UI 测试 - 登录页面
"""
import pytest


@pytest.fixture
def page(page):
    """页面 fixture"""
    return page


class TestLoginPage:
    """登录页面测试"""

    def test_should_display_login_form(self, page):
        """显示登录表单"""
        page.goto("http://localhost:3000/login")
        # 等待输入框出现 (n-input 渲染为 input)
        page.wait_for_selector('input[placeholder="请输入用户名"]', timeout=5000)
        page.wait_for_selector('input[placeholder="请输入密码"]', timeout=5000)
        # 等待登录按钮出现 (n-button 渲染为 button)
        page.wait_for_selector('button:has-text("登录")', timeout=5000)

    def test_should_login_with_valid_credentials(self, page):
        """使用有效凭据登录"""
        page.goto("http://localhost:3000/login")
        page.fill('input[placeholder="请输入用户名"]', "admin")
        page.fill('input[placeholder="请输入密码"]', "admin123")
        page.click('button:has-text("登录")')
        page.wait_for_url("**/dashboard", timeout=5000)

    def test_should_show_error_with_invalid_credentials(self, page):
        """无效凭据显示错误"""
        page.goto("http://localhost:3000/login")
        page.fill('input[placeholder="请输入用户名"]', "admin")
        page.fill('input[placeholder="请输入密码"]', "wrongpassword")
        page.click('button:has-text("登录")')
        page.wait_for_selector('.n-message, [role="alert"]', timeout=3000)
