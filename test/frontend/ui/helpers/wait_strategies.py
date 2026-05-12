"""
Wait Strategies - 等待策略工具
===============================
提供预定义的等待策略函数

用法：
    from helpers.wait_strategies import (
        wait_for_element_visible,
        wait_for_elements_count,
        wait_for_text,
    )

    wait_for_element_visible(page, "button:has-text('提交')", timeout=5000)
"""
import time
from typing import Callable, Optional, List
from playwright.sync_api import Page, Locator, TimeoutError as PlaywrightTimeoutError


# ============================================================================
# 元素等待策略
# ============================================================================

def wait_for_element_visible(
    page: Page,
    selector: str,
    timeout: int = 30000,
    state: str = "visible",
) -> Locator:
    """
    等待元素达到指定状态

    Args:
        page: Playwright Page 对象
        selector: CSS 选择器
        timeout: 超时时间（毫秒）
        state: 状态 (visible, hidden, attached, detached)

    Returns:
        Locator 对象
    """
    locator = page.locator(selector).first
    locator.wait_for(state=state, timeout=timeout)
    return locator


def wait_for_element_clickable(
    page: Page,
    selector: str,
    timeout: int = 30000,
) -> Locator:
    """
    等待元素可点击（可见且启用）

    Args:
        page: Playwright Page 对象
        selector: CSS 选择器
        timeout: 超时时间（毫秒）

    Returns:
        Locator 对象
    """
    locator = page.locator(selector).first
    locator.wait_for(state="visible", timeout=timeout)

    # 等待元素启用
    start_time = time.time()
    while time.time() - start_time < timeout / 1000:
        if not locator.is_disabled():
            return locator
        time.sleep(0.1)

    raise PlaywrightTimeoutError(f"Element not clickable: {selector}")


def wait_for_text(
    page: Page,
    selector: str,
    text: str,
    timeout: int = 30000,
) -> Locator:
    """
    等待元素包含指定文本

    Args:
        page: Playwright Page 对象
        selector: CSS 选择器
        text: 期望的文本
        timeout: 超时时间（毫秒）

    Returns:
        Locator 对象
    """
    locator = page.locator(selector).first
    start_time = time.time()

    while time.time() - start_time < timeout / 1000:
        try:
            element_text = locator.inner_text()
            if text in element_text:
                return locator
        except Exception:
            pass
        time.sleep(0.1)

    raise PlaywrightTimeoutError(f"Text '{text}' not found in: {selector}")


def wait_for_attribute(
    page: Page,
    selector: str,
    attribute: str,
    value: str,
    timeout: int = 30000,
) -> Locator:
    """
    等待元素属性匹配指定值

    Args:
        page: Playwright Page 对象
        selector: CSS 选择器
        attribute: 属性名
        value: 期望的属性值
        timeout: 超时时间（毫秒）

    Returns:
        Locator 对象
    """
    locator = page.locator(selector).first
    start_time = time.time()

    while time.time() - start_time < timeout / 1000:
        try:
            attr_val = locator.get_attribute(attribute)
            if attr_val and value in attr_val:
                return locator
        except Exception:
            pass
        time.sleep(0.1)

    raise PlaywrightTimeoutError(f"Attribute {attribute} not containing '{value}' in: {selector}")


def wait_for_elements_count(
    page: Page,
    selector: str,
    expected_count: int,
    timeout: int = 30000,
    greater_than: bool = False,
) -> List[Locator]:
    """
    等待元素数量匹配期望值

    Args:
        page: Playwright Page 对象
        selector: CSS 选择器
        expected_count: 期望数量
        timeout: 超时时间（毫秒）
        greater_than: True 表示 >= expected_count，False 表示 == expected_count

    Returns:
        Locator 列表
    """
    start_time = time.time()

    while time.time() - start_time < timeout / 1000:
        elements = page.query_selector_all(selector)
        count = len(elements)

        if greater_than and count >= expected_count:
            return elements
        elif not greater_than and count == expected_count:
            return elements

        time.sleep(0.1)

    elements = page.query_selector_all(selector)
    count = len(elements)
    raise PlaywrightTimeoutError(
        f"Expected {'at least ' if greater_than else ''}{expected_count} elements, found {count}"
    )


def wait_for_url(
    page: Page,
    pattern: str,
    timeout: int = 30000,
):
    """
    等待 URL 匹配模式

    Args:
        page: Playwright Page 对象
        pattern: URL 模式（支持 glob 和 regex）
        timeout: 超时时间（毫秒）
    """
    page.wait_for_url(pattern, timeout=timeout)


def wait_for_navigation(
    page: Page,
    wait_until: str = "networkidle",
    timeout: int = 30000,
):
    """
    等待导航完成

    Args:
        page: Playwright Page 对象
        wait_until: 等待状态 (load, domcontentloaded, networkidle)
        timeout: 超时时间（毫秒）
    """
    page.wait_for_load_state(wait_until, timeout=timeout)


# ============================================================================
# 条件等待策略
# ============================================================================

def wait_until(
    page: Page,
    condition: Callable[[], bool],
    timeout: int = 30000,
    poll_interval: int = 100,
) -> bool:
    """
    等待条件返回 True

    Args:
        page: Playwright Page 对象
        condition: 条件函数
        timeout: 超时时间（毫秒）
        poll_interval: 轮询间隔（毫秒）

    Returns:
        条件是否满足
    """
    start = time.time()
    while time.time() - start < timeout / 1000:
        try:
            if condition():
                return True
        except Exception:
            pass
        time.sleep(poll_interval / 1000)
    return False


def wait_for_function(
    page: Page,
    fn: str,
    timeout: int = 30000,
    *args,
) -> any:
    """
    等待 JS 函数返回 truthy 值

    Args:
        page: Playwright Page 对象
        fn: JavaScript 函数字符串
        timeout: 超时时间（毫秒）
        *args: 函数参数

    Returns:
        函数返回值
    """
    return page.wait_for_function(fn, timeout=timeout, *args)


# ============================================================================
# 复杂等待策略
# ============================================================================

def wait_for_dialog(
    page: Page,
    timeout: int = 30000,
    action: Callable[[], None] = None,
) -> Optional[Locator]:
    """
    等待对话框出现并返回

    Args:
        page: Playwright Page 对象
        timeout: 超时时间（毫秒）
        action: 触发对话框的动作（可选）

    Returns:
        对话框 Locator
    """
    if action:
        action()

    locator = page.locator(".el-dialog:visible, [role='dialog']").first
    locator.wait_for(state="visible", timeout=timeout)
    return locator


def wait_for消失在(
    page: Page,
    selector: str,
    timeout: int = 30000,
) -> bool:
    """
    等待元素消失

    Args:
        page: Playwright Page 对象
        selector: CSS 选择器
        timeout: 超时时间（毫秒）

    Returns:
        元素是否消失
    """
    try:
        locator = page.locator(selector).first
        locator.wait_for(state="hidden", timeout=timeout)
        return True
    except PlaywrightTimeoutError:
        return False


def wait_for_loader(
    page: Page,
    timeout: int = 30000,
    selector: str = ".el-loading-mask, .loading",
) -> bool:
    """
    等待加载指示器消失

    Args:
        page: Playwright Page 对象
        timeout: 超时时间（毫秒）
        selector: 加载器选择器

    Returns:
        加载是否完成
    """
    return wait_for消失在(page, selector, timeout)


def wait_for_table_load(
    page: Page,
    table_selector: str = ".el-table",
    timeout: int = 30000,
) -> List[Locator]:
    """
    等待表格加载完成

    Args:
        page: Playwright Page 对象
        table_selector: 表格选择器
        timeout: 超时时间（毫秒）

    Returns:
        表格行 Locator 列表
    """
    # 等待加载指示器消失
    wait_for_loader(page, timeout)

    # 等待表格行出现
    rows_selector = f"{table_selector} .el-table__body tr"
    return wait_for_elements_count(
        page,
        rows_selector,
        expected_count=0,
        timeout=timeout,
        greater_than=True,
    )


# ============================================================================
# 预定义超时配置
# ============================================================================

class TimeoutConfig:
    """预定义超时配置"""

    # 元素操作
    FAST = 5000       # 5 秒 - 快速操作
    NORMAL = 10000   # 10 秒 - 普通操作
    SLOW = 30000      # 30 秒 - 慢速操作
    VERY_SLOW = 60000 # 60 秒 - API 调用等

    # 导航
    NAVIGATION = 30000
    PAGE_LOAD = 30000
    NETWORK_IDLE = 30000

    # 网络响应
    API_RESPONSE = 10000
    WEBSOCKET = 5000
