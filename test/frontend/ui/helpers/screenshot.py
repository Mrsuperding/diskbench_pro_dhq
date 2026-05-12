"""
Screenshot Helper - 截图辅助工具
================================
提供截图功能封装

用法：
    from helpers.screenshot import ScreenshotHelper

    helper = ScreenshotHelper(page)
    helper.capture("before_action")
    helper.capture_full_page("full_page_shot")
"""
from pathlib import Path
from datetime import datetime
from typing import Optional
from playwright.sync_api import Page


class ScreenshotHelper:
    """
    截图辅助类

    提供便捷的截图功能，支持：
    - 普通截图和全页截图
    - 自定义文件名和目录
    - 自动时间戳命名
    - Allure 报告集成
    """

    DEFAULT_DIRECTORY = "test-results/screenshots"

    def __init__(self, page: Page, directory: str = DEFAULT_DIRECTORY):
        """
        初始化截图辅助类

        Args:
            page: Playwright Page 对象
            directory: 截图保存目录
        """
        self.page = page
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def capture(
        self,
        name: str = "screenshot",
        full_page: bool = False,
        timestamp: bool = True,
    ) -> Optional[Path]:
        """
        捕获截图

        Args:
            name: 截图名称
            full_page: 是否截取整个页面
            timestamp: 是否添加时间戳

        Returns:
            截图文件路径，失败返回 None
        """
        # 构建文件名
        if timestamp:
            ts = datetime.now().strftime("%H%M%S_%f")
            filename = f"{name}_{ts}.png"
        else:
            filename = f"{name}.png"

        filepath = self.directory / filename

        try:
            self.page.screenshot(path=str(filepath), full_page=full_page)
            print(f"\n[Screenshot] Captured: {filepath}")
            return filepath
        except Exception as e:
            print(f"\n[Screenshot] Failed to capture: {e}")
            return None

    def capture_full_page(self, name: str = "full_page") -> Optional[Path]:
        """截取整个页面"""
        return self.capture(name, full_page=True)

    def capture_element(
        self,
        selector: str,
        name: str = "element",
    ) -> Optional[Path]:
        """
        截取指定元素

        Args:
            selector: 元素选择器
            name: 截图名称

        Returns:
            截图文件路径
        """
        ts = datetime.now().strftime("%H%M%S_%f")
        filename = f"{name}_{ts}.png"
        filepath = self.directory / filename

        try:
            element = self.page.locator(selector).first
            element.screenshot(path=str(filepath))
            print(f"\n[Screenshot] Element captured: {filepath}")
            return filepath
        except Exception as e:
            print(f"\n[Screenshot] Failed to capture element: {e}")
            return None

    @staticmethod
    def capture_failure(
        page: Page,
        test_name: str,
        directory: str = DEFAULT_DIRECTORY,
    ) -> Optional[Path]:
        """
        捕获失败截图（静态方法）

        Args:
            page: Playwright Page 对象
            test_name: 测试名称
            directory: 保存目录

        Returns:
            截图文件路径
        """
        screenshot_dir = Path(directory)
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime("%H%M%S_%f")
        filename = f"{test_name}_failure_{ts}.png"
        filepath = screenshot_dir / filename

        try:
            page.screenshot(path=str(filepath), full_page=True)
            print(f"\n[Screenshot] Failure captured: {filepath}")
            return filepath
        except Exception as e:
            print(f"\n[Screenshot] Failed to capture failure: {e}")
            return None
