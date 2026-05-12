"""
Pytest Hooks - 测试生命周期钩子
=================================
提供测试执行各阶段的扩展功能：
- 测试开始/结束会话信息
- 失败时自动截图和 HTML 保存
- 性能数据收集
- 自定义报告生成

用法：
    # pytest 自动加载 hooks/pytest_hooks.py
    # 无需额外配置
"""
import pytest
import time
from pathlib import Path
from datetime import datetime
from playwright.sync_api import Page


# ============================================================================
# Session Hooks - 会话级别钩子
# ============================================================================

def pytest_sessionstart(session):
    """测试会话开始"""
    session.start_time = datetime.now()

    # 创建结果目录
    results_dir = Path("test-results")
    results_dir.mkdir(exist_ok=True)
    (results_dir / "screenshots").mkdir(exist_ok=True, exist_ok=True)
    (results_dir / "videos").mkdir(exist_ok=True, exist_ok=True)
    (results_dir / "html").mkdir(exist_ok=True, exist_ok=True)

    # 打印会话信息
    print("\n" + "=" * 70)
    print("DiskBench Pro UI Test Suite")
    print("=" * 70)
    print(f"Start Time: {session.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Test Items: {len(session.items)}")
    print("=" * 70)


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束"""
    duration = datetime.now() - session.start_time

    # 收集统计数据
    collected = len(session.items)
    passed = sum(1 for item in session.items
                  if hasattr(item, 'rep_call') and item.rep_call.passed)
    failed = sum(1 for item in session.items
                 if hasattr(item, 'rep_call') and item.rep_call.failed)
    skipped = sum(1 for item in session.items
                  if hasattr(item, 'rep_call') and item.rep_call.skipped)
    rerun = sum(1 for item in session.items
                if hasattr(item, 'rep_call') and item.rep_call.outcome == 'rerun')

    # 打印会话总结
    print("\n" + "=" * 70)
    print("Test Session Summary")
    print("=" * 70)
    print(f"Duration:   {duration}")
    print(f"Total:      {collected}")
    print(f"Passed:     {passed}")
    print(f"Failed:     {failed}")
    print(f"Skipped:    {skipped}")
    print(f"Rerun:      {rerun}")
    print(f"Exit Code:  {exitstatus}")
    print("=" * 70)

    # 打印失败测试列表
    if failed > 0:
        print("\nFailed Tests:")
        for item in session.items:
            if hasattr(item, 'rep_call') and item.rep_call.failed:
                print(f"  - {item.nodeid}")
        print()


# ============================================================================
# Item Hooks - 测试项级别钩子
# ============================================================================

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    在测试报告阶段保存失败信息

    为 failure_context fixture 提供失败信息访问
    """
    outcome = yield
    report = outcome.get_result()

    # 存储报告到 item，供 fixtures 访问
    setattr(item, f"rep_{report.when}", report)


def pytest_runtest_setup(item):
    """测试项设置阶段"""
    # 添加测试开始标记
    item._start_time = time.time()


def pytest_runtest_teardown(item, nextitem):
    """测试项拆卸阶段"""
    # 计算测试耗时
    if hasattr(item, '_start_time'):
        duration = time.time() - item._start_time
        if duration > 10:  # 超过 10 秒的测试标记为慢测试
            print(f"\n[SLOW TEST] {item.name} took {duration:.2f}s")


# ============================================================================
# Marker Hooks - 标记相关钩子
# ============================================================================

def pytest_configure(config):
    """Pytest 配置钩子"""
    # 注册自定义 markers
    config.addinivalue_line(
        "markers", "ui: UI 测试标记"
    )
    config.addinivalue_line(
        "markers", "api: API 测试标记"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试（执行时间 > 30s）"
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
    config.addinivalue_line(
        "markers", "e2e: 端到端测试"
    )
    config.addinivalue_line(
        "markers", "regression: 回归测试"
    )


def pytest_collection_modifyitems(session, config, items):
    """修改收集到的测试项"""
    for item in items:
        # 自动为慢测试添加标记
        if "slow" not in item.keywords:
            # 可以根据测试名称或路径自动标记
            pass


# ============================================================================
# Reporting Hooks - 报告相关钩子
# ============================================================================

@pytest.hookimpl(hookwrapper=True)
def pytest_report_teststatus(report):
    """自定义测试状态报告"""
    if report.when == "call":
        if report.passed:
            # 添加通过标记
            pass
        elif report.failed:
            # 检查是否为已知的基础设施错误
            if hasattr(report, 'longrepr'):
                # 可以在这里添加自定义错误分类
                pass


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """自定义终端总结"""
    # 添加自定义统计信息
    pass


# ============================================================================
# Fixture Hooks - Fixture 相关钩子
# ============================================================================

@pytest.hookimpl(tryfirst=True)
def pytest_fixture_setup(fixturedef, request):
    """Fixture 设置前调用"""
    pass


@pytest.hookimpl(trylast=True)
def pytest_fixture_teardown(fixturedef, request, nextitem):
    """Fixture 拆卸后调用"""
    pass
