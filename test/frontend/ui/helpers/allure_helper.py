"""
Allure Helper - Allure 报告辅助工具
====================================
提供 Allure 报告集成功能：
- 截图附件
- 控制台日志附件
- 环境信息添加
- 测试步骤标记

用法：
    from helpers.allure_helper import AllureHelper

    allure_helper = AllureHelper(page)
    allure_helper.attach_screenshot("login_screen")
    allure_helper.attach_console_logs()
    allure_helper.add_environment(app_url="http://localhost:3000")
"""
from typing import Optional, List
from playwright.sync_api import Page

try:
    import allure
    ALLURE_AVAILABLE = True
except ImportError:
    ALLURE_AVAILABLE = False


class AllureHelper:
    """
    Allure 报告辅助类

    提供便捷的 Allure 报告功能：
    - 截图附件
    - HTML 附件
    - 控制台日志附件
    - 环境信息
    - 测试步骤
    """

    def __init__(self, page: Page):
        """
        初始化 Allure 辅助类

        Args:
            page: Playwright Page 对象
        """
        self.page = page
        self._console_logs: List[str] = []

        if not ALLURE_AVAILABLE:
            import warnings
            warnings.warn("allure-pytest not installed. Some features will be disabled.")

    def attach_screenshot(
        self,
        name: str = "screenshot",
        full_page: bool = False,
    ) -> Optional[bytes]:
        """
        添加截图到 Allure 报告

        Args:
            name: 附件名称
            full_page: 是否截取整个页面

        Returns:
            截图二进制数据
        """
        if not ALLURE_AVAILABLE:
            return None

        try:
            screenshot_bytes = self.page.screenshot(full_page=full_page)
            allure.attach(
                screenshot_bytes,
                name=name,
                attachment_type=allure.attachment_type.PNG,
            )
            return screenshot_bytes
        except Exception as e:
            print(f"[Allure] Failed to attach screenshot: {e}")
            return None

    def attach_html(
        self,
        name: str = "page_html",
        content: Optional[str] = None,
    ) -> Optional[str]:
        """
        添加 HTML 内容到 Allure 报告

        Args:
            name: 附件名称
            content: HTML 内容（None 时自动获取当前页面）

        Returns:
            HTML 内容字符串
        """
        if not ALLURE_AVAILABLE:
            return None

        try:
            html_content = content or self.page.content()
            allure.attach(
                html_content,
                name=name,
                attachment_type=allure.attachment_type.HTML,
            )
            return html_content
        except Exception as e:
            print(f"[Allure] Failed to attach HTML: {e}")
            return None

    def attach_console_logs(self) -> List[str]:
        """
        添加控制台日志到 Allure 报告

        Returns:
            控制台日志列表
        """
        if not ALLURE_AVAILABLE:
            return []

        try:
            # 获取页面控制台消息
            logs = self.page.evaluate("""
                () => {
                    return window.__console_logs || [];
                }
            """)
            if logs:
                logs_text = "\n".join(logs)
                allure.attach(
                    logs_text,
                    name="console_logs",
                    attachment_type=allure.attachment_type.TEXT,
                )
            return logs
        except Exception as e:
            print(f"[Allure] Failed to attach console logs: {e}")
            return []

    def add_environment(self, **kwargs):
        """
        添加环境信息到 Allure 报告

        Args:
            **kwargs: 环境变量键值对
                app_url: 应用 URL
                browser: 浏览器类型
                version: 应用版本
        """
        if not ALLURE_AVAILABLE:
            return

        for key, value in kwargs.items():
            allure.environment(
                variable=key,
                value=value,
            )

    def add_test_parameter(self, name: str, value: str):
        """
        添加测试参数到 Allure 报告

        Args:
            name: 参数名称
            value: 参数值
        """
        if not ALLURE_AVAILABLE:
            return

        allure.parameter(name=name, value=value)

    @staticmethod
    def step(title: str):
        """
        创建 Allure 测试步骤装饰器

        用法：
            @AllureHelper.step("登录操作")
            def login():
                ...

        Args:
            title: 步骤标题
        """
        if not ALLURE_AVAILABLE:
            return lambda func: func

        return allure.step(title)

    @staticmethod
    def add_description(description: str):
        """
        添加测试描述

        Args:
            description: 描述文本
        """
        if not ALLURE_AVAILABLE:
            return

        allure.description(description)

    @staticmethod
    def add_severity(severity: str):
        """
        添加测试严重级别

        Args:
            severity: 级别 (trivial, minor, normal, blocker, critical)
        """
        if not ALLURE_AVAILABLE:
            return

        severity_map = {
            "trivial": allure.severity_level.TRIVIAL,
            "minor": allure.severity_level.MINOR,
            "normal": allure.severity_level.NORMAL,
            "blocker": allure.severity_level.BLOCKER,
            "critical": allure.severity_level.CRITICAL,
        }
        level = severity_map.get(severity.lower(), allure.severity_level.NORMAL)
        allure.severity(level)

    @staticmethod
    def add_feature(feature: str):
        """
        添加功能标签

        Args:
            feature: 功能名称
        """
        if not ALLURE_AVAILABLE:
            return

        allure.feature(feature)

    @staticmethod
    def add_story(story: str):
        """
        添加故事标签

        Args:
            story: 故事名称
        """
        if not ALLURE_AVAILABLE:
            return

        allure.story(story)

    @staticmethod
    def add_link(url: str, link_type: str = "link", name: str = None):
        """
        添加链接

        Args:
            url: 链接地址
            link_type: 链接类型 (link, issue, tms)
            name: 链接名称
        """
        if not ALLURE_AVAILABLE:
            return

        allure.link(url, link_type=link_type, name=name)


def attach_api_response(response_data: dict, name: str = "api_response"):
    """
    添加 API 响应到 Allure 报告（独立函数）

    Args:
        response_data: API 响应数据
        name: 附件名称
    """
    if not ALLURE_AVAILABLE:
        return

    import json
    try:
        formatted = json.dumps(response_data, indent=2, ensure_ascii=False)
        allure.attach(
            formatted,
            name=name,
            attachment_type=allure.attachment_type.JSON,
        )
    except Exception as e:
        print(f"[Allure] Failed to attach API response: {e}")


def attach_file(filepath: str, name: str = None, file_type: str = None):
    """
    添加文件到 Allure 报告（独立函数）

    Args:
        filepath: 文件路径
        name: 附件名称
        file_type: 文件类型 (text, json, html, xml, png, jpg, etc.)
    """
    if not ALLURE_AVAILABLE:
        return

    from pathlib import Path

    if not ALLURE_AVAILABLE:
        return

    try:
        path = Path(filepath)
        if not path.exists():
            print(f"[Allure] File not found: {filepath}")
            return

        content = path.read_bytes()
        attachment_type = getattr(allure.attachment_type, file_type.upper(), None) if file_type else None

        allure.attach(
            content,
            name=name or path.name,
            attachment_type=attachment_type,
        )
    except Exception as e:
        print(f"[Allure] Failed to attach file: {e}")
