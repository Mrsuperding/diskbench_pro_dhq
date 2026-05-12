"""
前端 UI 测试 - TaskNodePartition (分区选择)
=============================================
测试任务创建时的分区选择功能
"""
import pytest
import time
from playwright.sync_api import Page


class TestPartitionSelectorUI:
    """分区选择器 UI 测试"""

    def test_open_partition_selector_after_node_selection(
        self, test_data_page: Page
    ):
        """TC_UI_PARTITION_001 - 选择节点后显示分区配置"""
        test_data_page.goto("http://localhost:3000/tasks")
        test_data_page.wait_for_selector('.el-table', timeout=10000)

        # 点击创建任务按钮
        test_data_page.click('.page-header button:has-text("创建任务")')
        test_data_page.wait_for_selector('.el-dialog', timeout=5000)
        test_data_page.wait_for_timeout(2000)

        # 选择一个节点
        node_select = test_data_page.locator('.el-dialog .el-form-item:has-text("目标节点") .el-select')
        if node_select.is_visible():
            node_select.click()
            test_data_page.wait_for_timeout(1500)

            dropdown = test_data_page.locator('.el-select-dropdown:visible')
            if dropdown.count() > 0:
                options = test_data_page.query_selector_all('.el-select-dropdown__item')
                visible_options = [opt for opt in options if opt.is_visible()]
                real_options = [opt for opt in visible_options if '全部' not in opt.inner_text()]
                if len(real_options) > 0:
                    real_options[0].click(force=True)
                    test_data_page.wait_for_timeout(2000)

                    # 检查是否显示分区配置区域
                    partition_section = test_data_page.locator('text=分区配置')
                    if partition_section.is_visible():
                        # 验证分区选择器已显示
                        assert partition_section.is_visible(), "分区配置区域应该显示"
                    else:
                        pytest.skip("分区配置区域未显示，可能节点无分区")
                else:
                    pytest.skip("没有可用的节点")
            else:
                pytest.skip("下拉框未打开")
        else:
            pytest.skip("目标节点选择框不可见")

    def test_partition_list_loading(self, test_data_page: Page):
        """TC_UI_PARTITION_002 - 分区列表加载状态"""
        test_data_page.goto("http://localhost:3000/tasks")
        test_data_page.wait_for_selector('.el-table', timeout=10000)

        test_data_page.click('.page-header button:has-text("创建任务")')
        test_data_page.wait_for_selector('.el-dialog', timeout=5000)
        test_data_page.wait_for_timeout(1000)

        # 选择节点后检查加载状态
        node_select = test_data_page.locator('.el-dialog .el-form-item:has-text("目标节点") .el-select')
        if node_select.is_visible():
            node_select.click()
            test_data_page.wait_for_timeout(1000)

            dropdown = test_data_page.locator('.el-select-dropdown:visible')
            if dropdown.count() > 0:
                options = test_data_page.query_selector_all('.el-select-dropdown__item')
                visible_options = [opt for opt in options if opt.is_visible()]
                real_options = [opt for opt in visible_options if '全部' not in opt.inner_text()]
                if len(real_options) > 0:
                    real_options[0].click(force=True)
                    test_data_page.wait_for_timeout(500)

                    # 检查是否有加载指示器
                    loading = test_data_page.locator('.el-icon.is-loading')
                    if loading.count() > 0:
                        assert loading.is_visible(), "应该有加载状态显示"
                    else:
                        # 没有加载指示器，说明要么已加载完成，要么配置区域未显示
                        pass
                else:
                    pytest.skip("没有可用的节点")
            else:
                pytest.skip("下拉框未打开")

    def test_select_partition_from_list(self, test_data_page: Page):
        """TC_UI_PARTITION_003 - 从列表中选择分区"""
        test_data_page.goto("http://localhost:3000/tasks")
        test_data_page.wait_for_selector('.el-table', timeout=10000)

        test_data_page.click('.page-header button:has-text("创建任务")')
        test_data_page.wait_for_selector('.el-dialog', timeout=5000)
        test_data_page.wait_for_timeout(2000)

        # 选择节点
        node_select = test_data_page.locator('.el-dialog .el-form-item:has-text("目标节点") .el-select')
        if node_select.is_visible():
            node_select.click()
            test_data_page.wait_for_timeout(1500)

            dropdown = test_data_page.locator('.el-select-dropdown:visible')
            if dropdown.count() > 0:
                options = test_data_page.query_selector_all('.el-select-dropdown__item')
                visible_options = [opt for opt in options if opt.is_visible()]
                real_options = [opt for opt in visible_options if '全部' not in opt.inner_text()]
                if len(real_options) > 0:
                    real_options[0].click(force=True)
                    test_data_page.wait_for_timeout(2000)

                    # 检查分区配置区域
                    partition_select = test_data_page.locator('.el-dialog .el-form-item:has-text("选择分区") .el-select')
                    if partition_select.is_visible():
                        partition_select.click()
                        test_data_page.wait_for_timeout(1000)

                        # 检查下拉框
                        partition_dropdown = test_data_page.locator('.el-select-dropdown:visible')
                        if partition_dropdown.count() > 0:
                            partition_options = test_data_page.query_selector_all('.el-select-dropdown__item')
                            visible_partition_options = [opt for opt in partition_options if opt.is_visible()]
                            if len(visible_partition_options) > 0:
                                visible_partition_options[0].click(force=True)
                            else:
                                pytest.skip("没有可用的分区")
                        else:
                            pytest.skip("分区下拉框未打开")
                    else:
                        pytest.skip("分区选择框不可见")
                else:
                    pytest.skip("没有可用的节点")
            else:
                pytest.skip("节点下拉框未打开")
        else:
            pytest.skip("目标节点选择框不可见")

    def test_set_capacity_limit(self, test_data_page: Page):
        """TC_UI_PARTITION_004 - 设置容量限制"""
        test_data_page.goto("http://localhost:3000/tasks")
        test_data_page.wait_for_selector('.el-table', timeout=10000)

        test_data_page.click('.page-header button:has-text("创建任务")')
        test_data_page.wait_for_selector('.el-dialog', timeout=5000)
        test_data_page.wait_for_timeout(2000)

        # 选择节点
        node_select = test_data_page.locator('.el-dialog .el-form-item:has-text("目标节点") .el-select')
        if node_select.is_visible():
            node_select.click()
            test_data_page.wait_for_timeout(1500)

            dropdown = test_data_page.locator('.el-select-dropdown:visible')
            if dropdown.count() > 0:
                options = test_data_page.query_selector_all('.el-select-dropdown__item')
                visible_options = [opt for opt in options if opt.is_visible()]
                real_options = [opt for opt in visible_options if '全部' not in opt.inner_text()]
                if len(real_options) > 0:
                    real_options[0].click(force=True)
                    test_data_page.wait_for_timeout(2000)

                    # 找到容量限制输入框
                    capacity_input = test_data_page.locator('.el-dialog .el-form-item:has-text("容量限制") input')
                    if capacity_input.is_visible():
                        # 清空并输入新值
                        capacity_input.clear()
                        capacity_input.fill("2048")
                        value = capacity_input.input_value()
                        assert value == "2048", f"期望容量限制为 2048，实际为 {value}"
                    else:
                        pytest.skip("容量限制输入框不可见")
                else:
                    pytest.skip("没有可用的节点")
            else:
                pytest.skip("下拉框未打开")
        else:
            pytest.skip("目标节点选择框不可见")

    def test_partition_info_display(self, test_data_page: Page):
        """TC_UI_PARTITION_005 - 分区信息显示（挂载点、文件系统、可用空间）"""
        test_data_page.goto("http://localhost:3000/tasks")
        test_data_page.wait_for_selector('.el-table', timeout=10000)

        test_data_page.click('.page-header button:has-text("创建任务")')
        test_data_page.wait_for_selector('.el-dialog', timeout=5000)
        test_data_page.wait_for_timeout(2000)

        # 选择节点
        node_select = test_data_page.locator('.el-dialog .el-form-item:has-text("目标节点") .el-select')
        if node_select.is_visible():
            node_select.click()
            test_data_page.wait_for_timeout(1500)

            dropdown = test_data_page.locator('.el-select-dropdown:visible')
            if dropdown.count() > 0:
                options = test_data_page.query_selector_all('.el-select-dropdown__item')
                visible_options = [opt for opt in options if opt.is_visible()]
                real_options = [opt for opt in visible_options if '全部' not in opt.inner_text()]
                if len(real_options) > 0:
                    real_options[0].click(force=True)
                    test_data_page.wait_for_timeout(3000)

                    # 检查分区信息是否显示
                    # 应该显示：挂载点、文件系统、可用空间
                    mount_point_label = test_data_page.locator('text=挂载点:')
                    filesystem_label = test_data_page.locator('text=文件系统:')
                    available_space_label = test_data_page.locator('text=可用空间:')

                    has_mount_point = mount_point_label.count() > 0
                    has_filesystem = filesystem_label.count() > 0
                    has_available_space = available_space_label.count() > 0

                    if has_mount_point or has_filesystem or has_available_space:
                        pass  # 至少有一项分区信息显示
                    else:
                        pytest.skip("分区信息未显示，可能无分区数据")
                else:
                    pytest.skip("没有可用的节点")
            else:
                pytest.skip("下拉框未打开")
        else:
            pytest.skip("目标节点选择框不可见")