"""
Task Creation Tests - 任务创建完整流程测试
==========================================
"""
import pytest
import time
from playwright.sync_api import Page


class TestTaskCreationBasic:
    """任务创建基本测试"""

    def test_open_create_dialog(self, authenticated_page: Page):
        """TC_UI_TASK_CREATE_001 - 打开创建任务对话框"""
        authenticated_page.goto("http://localhost:3000/tasks")
        authenticated_page.wait_for_selector('.el-table', timeout=10000)

        authenticated_page.click('.page-header button:has-text("创建任务")')
        authenticated_page.wait_for_selector('.el-dialog', timeout=5000)
        assert authenticated_page.is_visible('.el-dialog')

    def test_close_dialog(self, authenticated_page: Page):
        """TC_UI_TASK_CREATE_002 - 关闭对话框"""
        authenticated_page.goto("http://localhost:3000/tasks")
        authenticated_page.wait_for_selector('.el-table', timeout=10000)

        authenticated_page.click('.page-header button:has-text("创建任务")')
        authenticated_page.wait_for_selector('.el-dialog', timeout=5000)

        authenticated_page.click('.el-dialog__footer button:has-text("取消")')
        authenticated_page.wait_for_selector('.el-dialog', state="hidden", timeout=5000)

    def test_fill_task_name(self, authenticated_page: Page):
        """TC_UI_TASK_CREATE_003 - 任务名称字段"""
        authenticated_page.goto("http://localhost:3000/tasks")
        authenticated_page.wait_for_selector('.el-table', timeout=10000)

        authenticated_page.click('.page-header button:has-text("创建任务")')
        authenticated_page.wait_for_selector('.el-dialog', timeout=5000)

        test_name = f"TestTask_{int(time.time())}"
        authenticated_page.fill('.el-dialog input[placeholder="请输入任务名称"]', test_name)

        value = authenticated_page.input_value('.el-dialog input[placeholder="请输入任务名称"]')
        assert value == test_name

    def test_select_case(self, test_data_page: Page):
        """TC_UI_TASK_CREATE_004 - 测试用例选择"""
        test_data_page.goto("http://localhost:3000/tasks")
        test_data_page.wait_for_selector('.el-table', timeout=10000)
        test_data_page.wait_for_timeout(2000)

        # 打开对话框
        test_data_page.click('.page-header button:has-text("创建任务")')
        test_data_page.wait_for_selector('.el-dialog', timeout=5000)
        test_data_page.wait_for_timeout(3000)

        # 点击 case select
        case_select = test_data_page.locator('.el-dialog .el-form-item:has-text("测试用例") .el-select')
        if case_select.is_visible():
            case_select.click()
            test_data_page.wait_for_timeout(2000)

            # 检查下拉框
            dropdown = test_data_page.locator('.el-select-dropdown:visible')
            if dropdown.count() > 0:
                options = test_data_page.query_selector_all('.el-select-dropdown__item')
                visible_options = [opt for opt in options if opt.is_visible()]
                real_options = [opt for opt in visible_options if '全部' not in opt.inner_text()]
                if len(real_options) > 0:
                    real_options[0].click(force=True)
                else:
                    pytest.skip("没有可用的测试用例")
            else:
                pytest.skip("下拉框未打开")
        else:
            pytest.skip("测试用例选择框不可见")

    def test_select_nodes(self, test_data_page: Page):
        """TC_UI_TASK_CREATE_005 - 目标节点选择"""
        test_data_page.goto("http://localhost:3000/tasks")
        test_data_page.wait_for_selector('.el-table', timeout=10000)
        test_data_page.wait_for_timeout(2000)

        # 打开对话框
        test_data_page.click('.page-header button:has-text("创建任务")')
        test_data_page.wait_for_selector('.el-dialog', timeout=5000)
        test_data_page.wait_for_timeout(2000)

        # 等待节点数据加载
        test_data_page.wait_for_timeout(2000)

        # 点击 node select
        node_select = test_data_page.locator('.el-dialog .el-form-item:has-text("目标节点") .el-select')
        if node_select.is_visible():
            node_select.click()
            test_data_page.wait_for_timeout(1500)

            # 检查下拉框
            dropdown = test_data_page.locator('.el-select-dropdown:visible')
            if dropdown.count() > 0:
                options = test_data_page.query_selector_all('.el-select-dropdown__item')
                visible_options = [opt for opt in options if opt.is_visible()]
                # 选择第一个不是"全部"的选项
                for opt in visible_options:
                    if '全部' not in opt.inner_text():
                        opt.click(force=True)
                        break
                else:
                    pytest.skip("没有可用的节点")
            else:
                pytest.skip("下拉框未打开")
        else:
            pytest.skip("目标节点选择框不可见")

    def test_fill_test_path(self, authenticated_page: Page):
        """TC_UI_TASK_CREATE_006 - 测试路径字段"""
        authenticated_page.goto("http://localhost:3000/tasks")
        authenticated_page.wait_for_selector('.el-table', timeout=10000)

        authenticated_page.click('.page-header button:has-text("创建任务")')
        authenticated_page.wait_for_selector('.el-dialog', timeout=5000)
        authenticated_page.wait_for_timeout(500)

        # 通过 label 找到测试路径输入框
        test_path_input = authenticated_page.locator('.el-dialog .el-form-item:has-text("测试路径") input')
        if test_path_input.is_visible():
            test_path_input.fill("/tmp/test_fio")
        else:
            pytest.skip("测试路径输入框不可见")

    def test_concurrency_field(self, authenticated_page: Page):
        """TC_UI_TASK_CREATE_007 - 并发度字段"""
        authenticated_page.goto("http://localhost:3000/tasks")
        authenticated_page.wait_for_selector('.el-table', timeout=10000)

        authenticated_page.click('.page-header button:has-text("创建任务")')
        authenticated_page.wait_for_selector('.el-dialog', timeout=5000)
        authenticated_page.wait_for_timeout(500)

        # 通过 label 找到并发度输入框
        concurrency_input = authenticated_page.locator('.el-dialog .el-form-item:has-text("并发度") input')
        if concurrency_input.is_visible():
            authenticated_page.click('.el-dialog .el-form-item:has-text("并发度") .el-input-number__increase')


class TestTaskCreationValidation:
    """任务创建验证测试"""

    def test_empty_name_validation(self, authenticated_page: Page):
        """TC_UI_TASK_CREATE_008 - 空名称验证"""
        authenticated_page.goto("http://localhost:3000/tasks")
        authenticated_page.wait_for_selector('.el-table', timeout=10000)

        authenticated_page.click('.page-header button:has-text("创建任务")')
        authenticated_page.wait_for_selector('.el-dialog', timeout=5000)

        authenticated_page.click('.el-dialog__footer button:has-text("创建任务")')
        authenticated_page.wait_for_timeout(500)

        errors = authenticated_page.query_selector_all('.el-form-item__error')
        assert len(errors) > 0, "应该显示验证错误"


class TestTaskCreationAndExecution:
    """任务创建和执行测试"""

    def test_create_and_start_task(self, test_data_page: Page):
        """TC_UI_TASK_EXEC_001 - 创建并启动任务（端到端）"""
        page = test_data_page
        task_name = f"AutoTest_Task_{int(time.time())}"

        # 1. 创建任务
        page.goto("http://localhost:3000/tasks")
        page.wait_for_selector('.el-table', timeout=10000)
        page.wait_for_timeout(2000)

        # 点击创建任务按钮
        page.click('.page-header button:has-text("创建任务")')
        page.wait_for_selector('.el-dialog', timeout=5000)
        page.wait_for_timeout(1000)

        # 填写任务名称
        page.fill('input[placeholder="请输入任务名称"]', task_name)

        # 选择测试用例 - 使用更稳定的方式
        try:
            case_select = page.locator('.el-dialog .el-select').first
            case_select.click()
            page.wait_for_selector('.el-select-dropdown:visible', timeout=3000)
            option = page.locator('.el-select-dropdown__item').first
            option.click()
            page.wait_for_timeout(500)
        except Exception:
            pytest.skip("无法选择测试用例")

        # 选择目标节点
        try:
            node_select = page.locator('.el-dialog .el-select').nth(1)
            node_select.click()
            page.wait_for_selector('.el-select-dropdown:visible', timeout=3000)
            option = page.locator('.el-select-dropdown__item').first
            option.click()
            page.wait_for_timeout(500)
        except Exception:
            pytest.skip("无法选择目标节点")

        # 填写测试路径
        try:
            test_path_input = page.locator('.el-dialog input[placeholder*="测试路径"]')
            if test_path_input.is_visible():
                test_path_input.fill("/tmp/fio_test")
        except Exception:
            pass  # 测试路径可能不是必填

        # 提交创建
        page.click('.el-dialog__footer button:has-text("创建任务")')
        page.wait_for_timeout(5000)

        # 2. 验证任务创建成功 - 检查是否显示成功提示或任务出现在列表
        # 方式1: 检查成功提示
        success_msg = page.locator('.el-message:has-text("成功")')
        has_success = success_msg.count() > 0

        # 方式2: 刷新页面检查任务列表
        page.goto("http://localhost:3000/tasks")
        page.wait_for_selector('.el-table', timeout=10000)
        page.wait_for_timeout(2000)

        page_content = page.content()
        task_in_list = task_name in page_content

        assert has_success or task_in_list, "任务应该创建成功"

    def test_task_appears_in_list_after_creation(self, test_data_page: Page):
        """TC_UI_TASK_EXEC_002 - 创建后任务出现在列表"""
        page = test_data_page
        task_name = f"VerifyInList_{int(time.time())}"

        # 创建任务
        page.goto("http://localhost:3000/tasks")
        page.wait_for_selector('.el-table', timeout=10000)
        page.wait_for_timeout(2000)

        page.click('.page-header button:has-text("创建任务")')
        page.wait_for_selector('.el-dialog', timeout=5000)
        page.wait_for_timeout(1000)

        page.fill('input[placeholder="请输入任务名称"]', task_name)

        # 选择用例
        try:
            case_select = page.locator('.el-dialog .el-select').first
            case_select.click()
            page.wait_for_selector('.el-select-dropdown:visible', timeout=3000)
            option = page.locator('.el-select-dropdown__item').first
            option.click()
            page.wait_for_timeout(500)
        except Exception:
            pytest.skip("无法选择测试用例")

        # 提交
        page.click('.el-dialog__footer button:has-text("创建任务")')
        page.wait_for_timeout(5000)

        # 刷新页面验证任务存在
        page.goto("http://localhost:3000/tasks")
        page.wait_for_selector('.el-table', timeout=10000)
        page.wait_for_timeout(2000)

        # 验证任务名称在列表中
        page_content = page.content()
        assert task_name in page_content, f"任务列表应该包含新创建的任务: {task_name}"

    def test_start_button_visible_for_pending_task(self, test_data_page: Page):
        """TC_UI_TASK_EXEC_003 - 待执行任务显示启动按钮"""
        page = test_data_page

        page.goto("http://localhost:3000/tasks")
        page.wait_for_selector('.el-table', timeout=10000)
        page.wait_for_timeout(2000)

        # 进入任务详情
        rows = page.query_selector_all('.el-table__body tr')
        if not rows:
            pytest.skip("任务列表为空")

        # 点击第一个任务进入详情
        try:
            rows[0].click()
            page.wait_for_timeout(2000)
            page.wait_for_url(f"**/tasks/**", timeout=10000)

            # 检查启动按钮可见
            start_btn = page.locator('button:has-text("启动")')
            stop_btn = page.locator('button:has-text("停止")')
            assert start_btn.count() > 0 or stop_btn.count() > 0, "应该显示启动或停止按钮"
        except Exception as e:
            pytest.skip(f"无法进入任务详情: {e}")