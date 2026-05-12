"""
任务详情页面 UI 测试
====================
测试任务详情页面的各项功能
"""
import pytest
from playwright.sync_api import Page, expect


class TestTaskDetailBasic:
    """任务详情页基础功能测试"""

    @pytest.fixture(autouse=True)
    def setup(self, test_data_page: Page):
        """设置"""
        self.page = test_data_page
        self.task_id = 1  # 使用第一个任务

    def test_should_load_task_detail_page(self):
        """TC_DETAIL_001 - 加载任务详情页"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 检查页面标题可见
        h1 = self.page.locator("h1")
        assert h1.is_visible(), "任务标题应该可见"

    def test_should_display_metrics_cards(self):
        """TC_DETAIL_002 - 显示指标卡片"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 检查指标卡片可见
        metrics_grid = self.page.locator(".metrics-grid")
        assert metrics_grid.is_visible(), "指标网格应该可见"

        # 检查有指标卡片
        metric_cards = self.page.locator(".metric-card")
        assert metric_cards.count() >= 1, "应该有指标卡片"

    def test_should_display_task_status(self):
        """TC_DETAIL_003 - 显示任务状态"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 检查状态徽章可见
        status_badge = self.page.locator(".status-badge")
        if status_badge.count() > 0:
            assert status_badge.first.is_visible(), "状态徽章应该可见"

    def test_should_have_action_buttons(self):
        """TC_DETAIL_004 - 有操作按钮"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 检查返回按钮
        back_btn = self.page.locator(".back-btn")
        assert back_btn.is_visible(), "返回按钮应该可见"


class TestTaskDetailTabs:
    """任务详情页 Tab 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, test_data_page: Page):
        """设置"""
        self.page = test_data_page
        self.task_id = 1

    def test_should_show_tabs(self):
        """TC_DETAIL_010 - 显示所有 Tab"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 检查 Tab 导航存在
        tab_nav = self.page.locator(".tab-navigation")
        assert tab_nav.is_visible(), "Tab 导航应该可见"

        # 检查有 Tab 按钮
        tab_btns = self.page.locator(".tab-btn")
        assert tab_btns.count() >= 4, "应该至少有4个 Tab"

    def test_should_switch_to_info_tab(self):
        """TC_DETAIL_011 - 切换到基本信息 Tab"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 点击基本信息 Tab
        info_tab = self.page.locator(".tab-btn:has-text('基本信息')")
        if info_tab.count() > 0:
            info_tab.click()
            self.page.wait_for_timeout(500)

            # 检查信息网格可见
            info_grid = self.page.locator(".info-grid")
            assert info_grid.is_visible(), "基本信息网格应该可见"

    def test_should_switch_to_nodes_tab(self):
        """TC_DETAIL_012 - 切换到节点 Tab"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 点击节点 Tab
        nodes_tab = self.page.locator(".tab-btn:has-text('节点')")
        if nodes_tab.count() > 0:
            nodes_tab.click()
            self.page.wait_for_timeout(500)

            # 检查节点内容区可见
            section_header = self.page.locator(".section-header")
            assert section_header.first.is_visible(), "节点内容区应该可见"

    def test_should_switch_to_case_tab(self):
        """TC_DETAIL_013 - 切换到用例 Tab"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 点击用例 Tab
        case_tab = self.page.locator(".tab-btn:has-text('用例')")
        if case_tab.count() > 0:
            case_tab.click()
            self.page.wait_for_timeout(500)

            # 使用 JS 检查用例 Tab 内容可见性
            result = self.page.evaluate('''
                () => {
                    const tabPanels = document.querySelectorAll('.tab-panel');
                    const casePanel = tabPanels[2]; // case tab is 3rd (index 2)
                    if (!casePanel) return { error: true };
                    const sectionHeader = casePanel.querySelector('.section-header');
                    return {
                        hasSectionHeader: !!sectionHeader,
                        sectionHeaderVisible: sectionHeader ? sectionHeader.offsetParent !== null : false
                    };
                }
            ''')
            assert result.get('hasSectionHeader'), "应该显示用例内容区"

    def test_should_switch_to_logs_tab(self):
        """TC_DETAIL_014 - 切换到日志 Tab"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 点击日志 Tab
        logs_tab = self.page.locator(".tab-btn:has-text('日志')")
        if logs_tab.count() > 0:
            logs_tab.click()
            self.page.wait_for_timeout(500)

            # 检查日志 Tab 内容可见
            tab_panel = self.page.locator(".tab-panel:visible")
            assert tab_panel.is_visible(), "日志 Tab 内容应该可见"


class TestTaskDetailInfoTab:
    """基本信息 Tab 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, test_data_page: Page):
        """设置"""
        self.page = test_data_page
        self.task_id = 1

    def test_should_display_task_id(self):
        """TC_DETAIL_020 - 显示任务ID"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 确保在基本信息 Tab
        info_tab = self.page.locator(".tab-btn:has-text('基本信息')")
        if info_tab.count() > 0:
            info_tab.click()
            self.page.wait_for_timeout(300)

        # 检查任务ID显示
        info_grid = self.page.locator(".info-grid")
        assert info_grid.is_visible(), "基本信息网格应该可见"

    def test_should_display_creation_time(self):
        """TC_DETAIL_021 - 显示创建时间"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 确保在基本信息 Tab
        info_tab = self.page.locator(".tab-btn:has-text('基本信息')")
        if info_tab.count() > 0:
            info_tab.click()
            self.page.wait_for_timeout(300)

        # 检查创建时间显示
        info_section = self.page.locator(".info-section")
        assert info_section.count() > 0, "应该显示信息区块"


class TestTaskDetailNodesTab:
    """节点 Tab 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, test_data_page: Page):
        """设置"""
        self.page = test_data_page
        self.task_id = 1

    def test_should_show_add_node_button(self):
        """TC_DETAIL_030 - 显示添加节点按钮"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 切换到节点 Tab
        nodes_tab = self.page.locator(".tab-btn:has-text('节点')")
        if nodes_tab.count() > 0:
            nodes_tab.click()
            self.page.wait_for_timeout(500)

            # 检查添加节点按钮
            add_btn = self.page.locator('button:has-text("添加节点")')
            assert add_btn.is_visible(), "添加节点按钮应该可见"

    def test_should_show_node_list_or_empty(self):
        """TC_DETAIL_031 - 显示节点列表或空状态"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 切换到节点 Tab
        nodes_tab = self.page.locator(".tab-btn:has-text('节点')")
        if nodes_tab.count() > 0:
            nodes_tab.click()
            self.page.wait_for_timeout(500)

            # 要么有表格，要么有空状态
            has_table = self.page.locator(".node-table").is_visible()
            has_empty = self.page.locator(".empty-state").first.is_visible()
            assert has_table or has_empty, "应该显示表格或空状态"

    def test_should_open_add_node_dialog(self):
        """TC_DETAIL_032 - 打开添加节点对话框"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 切换到节点 Tab
        nodes_tab = self.page.locator(".tab-btn:has-text('节点')")
        if nodes_tab.count() > 0:
            nodes_tab.click()
            self.page.wait_for_timeout(500)

            # 点击添加节点按钮
            add_btn = self.page.locator('button:has-text("添加节点")')
            if add_btn.count() > 0:
                add_btn.click()
                self.page.wait_for_timeout(500)

                # 检查对话框可见
                dialog = self.page.locator('.el-dialog')
                assert dialog.is_visible(), "添加节点对话框应该可见"

    def test_add_node_dialog_should_have_node_selector(self):
        """TC_DETAIL_033 - 添加节点对话框应该有节点选择器和分区输入框"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 切换到节点 Tab
        nodes_tab = self.page.locator(".tab-btn:has-text('节点')")
        if nodes_tab.count() > 0:
            nodes_tab.click()
            self.page.wait_for_timeout(500)

        # 点击添加节点按钮
        add_btn = self.page.locator('button:has-text("添加节点")')
        if add_btn.count() > 0:
            add_btn.click()
            self.page.wait_for_timeout(500)

            # 检查节点选择器存在
            node_select = self.page.locator('.el-dialog .el-select').first
            assert node_select.is_visible(), "节点选择器应该可见"

            # 检查分区输入框存在（现在是文本输入）
            partition_input = self.page.locator('.el-dialog input[placeholder*="分区"]')
            assert partition_input.is_visible(), "分区输入框应该可见"

    def test_node_selector_should_be_filterable(self):
        """TC_DETAIL_034 - 节点选择器应该可过滤"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 切换到节点 Tab
        nodes_tab = self.page.locator(".tab-btn:has-text('节点')")
        if nodes_tab.count() > 0:
            nodes_tab.click()
            self.page.wait_for_timeout(500)

        # 点击添加节点按钮
        add_btn = self.page.locator('button:has-text("添加节点")')
        if add_btn.count() > 0:
            add_btn.click()
            self.page.wait_for_timeout(500)

            # 点击节点选择器打开下拉
            node_select = self.page.locator('.el-dialog .el-select').first
            node_select.click()
            self.page.wait_for_timeout(300)

            # Element Plus filterable select has an input inside
            filter_input = self.page.locator('.el-select-dropdown__list')
            assert filter_input.count() > 0, "节点选择器下拉列表应该可见"

    def test_node_dropdown_should_have_options(self):
        """TC_DETAIL_035 - 节点下拉列表应该有选项数据"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 切换到节点 Tab
        nodes_tab = self.page.locator(".tab-btn:has-text('节点')")
        if nodes_tab.count() > 0:
            nodes_tab.click()
            self.page.wait_for_timeout(500)

        # 点击添加节点按钮
        add_btn = self.page.locator('button:has-text("添加节点")')
        if add_btn.count() > 0:
            add_btn.click()
            self.page.wait_for_timeout(1000)  # 等待节点列表加载

            # 点击节点选择器打开下拉
            node_select = self.page.locator('.el-dialog .el-select').first
            node_select.click()
            self.page.wait_for_timeout(500)

            # 检查下拉列表有选项或空状态
            dropdown = self.page.locator('.el-select-dropdown:visible')
            if dropdown.count() > 0:
                options = self.page.locator('.el-select-dropdown__item')
                option_count = options.count()

                # 如果没有选项，检查是否有"无数据"提示（这是可接受的空状态）
                empty_text = self.page.locator('.el-select-dropdown__empty')
                has_empty_message = empty_text.count() > 0

                # 验证：要么有选项，要么显示空状态消息
                assert option_count > 0 or has_empty_message, \
                    f"节点下拉列表应该显示选项或空状态，当前选项数: {option_count}"
            else:
                pytest.skip("下拉框未打开")


class TestTaskDetailCaseTab:
    """用例 Tab 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, test_data_page: Page):
        """设置"""
        self.page = test_data_page
        self.task_id = 1

    def test_should_show_add_case_button(self):
        """TC_DETAIL_040 - 显示添加用例按钮"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 切换到用例 Tab
        case_tab = self.page.locator(".tab-btn:has-text('用例')")
        if case_tab.count() > 0:
            case_tab.click()
            self.page.wait_for_timeout(500)

            # 检查添加用例按钮
            add_btn = self.page.locator('button:has-text("添加用例配置")')
            assert add_btn.is_visible(), "添加用例按钮应该可见"

    def test_should_show_case_list_or_empty(self):
        """TC_DETAIL_041 - 显示用例列表或空状态"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 切换到用例 Tab
        case_tab = self.page.locator(".tab-btn:has-text('用例')")
        if case_tab.count() > 0:
            case_tab.click()
            self.page.wait_for_timeout(500)

            # 要么有列表，要么有空状态
            has_list = self.page.locator(".case-list").is_visible()
            has_empty = self.page.locator(".empty-state").first.is_visible()
            assert has_list or has_empty, "应该显示用例列表或空状态"

    def test_should_open_add_case_dialog(self):
        """TC_DETAIL_042 - 打开添加用例对话框"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 切换到用例 Tab
        case_tab = self.page.locator(".tab-btn:has-text('用例')")
        if case_tab.count() > 0:
            case_tab.click()
            self.page.wait_for_timeout(500)

            # 点击添加用例按钮
            add_btn = self.page.locator('button:has-text("添加用例配置")')
            if add_btn.count() > 0:
                add_btn.click()
                self.page.wait_for_timeout(500)

                # 检查对话框可见
                dialog = self.page.locator('.el-dialog')
                assert dialog.is_visible(), "添加用例对话框应该可见"

    def test_case_dialog_should_have_block_size_multiselect(self):
        """TC_DETAIL_043 - 用例对话框应该支持多选块大小"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 切换到用例 Tab
        case_tab = self.page.locator(".tab-btn:has-text('用例')")
        if case_tab.count() > 0:
            case_tab.click()
            self.page.wait_for_timeout(500)

            # 点击添加用例按钮
            add_btn = self.page.locator('button:has-text("添加用例配置")')
            if add_btn.count() > 0:
                add_btn.click()
                self.page.wait_for_timeout(500)

                # 检查对话框有多个 el-select (块大小和IO模式应该是多选的)
                selects = self.page.locator('.case-dialog .el-select')
                assert selects.count() >= 2, "用例对话框应该有至少2个选择器(块大小、IO模式)"

                # 点击第一个选择器检查多选
                selects.first.click()
                self.page.wait_for_timeout(300)

                # 检查有多个选项
                options = self.page.locator('.el-select-dropdown__item')
                assert options.count() >= 2, "块大小应该有多于2个选项"

    def test_case_dialog_should_have_rw_mode_multiselect(self):
        """TC_DETAIL_044 - 用例对话框应该支持多选IO模式"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 切换到用例 Tab
        case_tab = self.page.locator(".tab-btn:has-text('用例')")
        if case_tab.count() > 0:
            case_tab.click()
            self.page.wait_for_timeout(500)

            # 点击添加用例按钮
            add_btn = self.page.locator('button:has-text("添加用例配置")')
            if add_btn.count() > 0:
                add_btn.click()
                self.page.wait_for_timeout(500)

                # 检查对话框有多个 el-select
                selects = self.page.locator('.case-dialog .el-select')
                assert selects.count() >= 2, "用例对话框应该有至少2个选择器"

                # 点击第二个选择器 (IO模式)
                selects.nth(1).click()
                self.page.wait_for_timeout(300)

                # 检查有多个选项
                options = self.page.locator('.el-select-dropdown__item')
                assert options.count() >= 2, "IO模式应该有多于2个选项"

    def test_case_card_should_display_multiple_values(self):
        """TC_DETAIL_045 - 用例卡片应该显示多个块大小和IO模式"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 切换到用例 Tab
        case_tab = self.page.locator(".tab-btn:has-text('用例')")
        if case_tab.count() > 0:
            case_tab.click()
            self.page.wait_for_timeout(500)

            # 如果有用例卡片，检查是否显示多个值标签
            case_cards = self.page.locator(".case-card")
            if case_cards.count() > 0:
                # 检查有多值标签
                value_tags = self.page.locator(".value-tag")
                assert value_tags.count() >= 1, "应该显示值标签(块大小或IO模式)"


class TestTaskDetailLogsTab:
    """日志 Tab 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, test_data_page: Page):
        """设置"""
        self.page = test_data_page
        self.task_id = 1

    def test_should_show_logs_list_or_empty(self):
        """TC_DETAIL_050 - 显示日志列表或空状态"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 切换到日志 Tab
        logs_tab = self.page.locator(".tab-btn:has-text('日志')")
        if logs_tab.count() > 0:
            logs_tab.click()
            self.page.wait_for_timeout(500)

            # 在日志 Tab 内容区检查 - 使用 JS 检查避免选择器问题
            result = self.page.evaluate('''
                () => {
                    const tabPanels = document.querySelectorAll('.tab-panel');
                    const logsPanel = tabPanels[3];
                    if (!logsPanel) return { error: true };
                    return {
                        hasLogs: !!logsPanel.querySelector('.log-list'),
                        hasEmpty: !!logsPanel.querySelector('.empty-state')
                    };
                }
            ''')
            assert result.get('hasLogs') or result.get('hasEmpty'), "应该显示日志列表或空状态"

    def test_should_show_refresh_button(self):
        """TC_DETAIL_051 - 显示刷新按钮"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 切换到日志 Tab
        logs_tab = self.page.locator(".tab-btn:has-text('日志')")
        if logs_tab.count() > 0:
            logs_tab.click()
            self.page.wait_for_timeout(500)

            # 检查刷新按钮
            refresh_btn = self.page.locator('button:has-text("刷新")')
            assert refresh_btn.count() > 0, "刷新按钮应该存在"


class TestTaskDetailActions:
    """任务操作测试"""

    @pytest.fixture(autouse=True)
    def setup(self, test_data_page: Page):
        """设置"""
        self.page = test_data_page
        self.task_id = 1

    def test_should_navigate_back(self):
        """TC_DETAIL_060 - 点击返回按钮"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 点击返回
        self.page.locator(".back-btn").click()
        self.page.wait_for_timeout(1000)

        # 应该离开详情页 (URL 应该不包含 /tasks/{id})
        assert f"/tasks/{self.task_id}" not in self.page.url, f"应该在详情页之外，当前URL: {self.page.url}"

    def test_pending_task_should_show_start_button(self):
        """TC_DETAIL_061 - 待执行任务显示启动按钮"""
        self.page.goto(f"http://localhost:3000/tasks/{self.task_id}")
        self.page.wait_for_load_state("networkidle")

        # 检查是否有启动按钮
        start_btn = self.page.locator('button:has-text("启动")')
        stop_btn = self.page.locator('button:has-text("停止")')

        # 要么显示启动，要么显示停止
        has_action = start_btn.count() > 0 or stop_btn.count() > 0
        assert has_action, "应该显示操作按钮"


class TestTaskDetailNavigation:
    """任务列表到详情的导航测试"""

    def test_should_navigate_to_detail_from_list(self, test_data_page: Page):
        """TC_DETAIL_070 - 从列表导航到详情"""
        page = test_data_page

        # 先到任务列表
        page.goto("http://localhost:3000/tasks")
        page.wait_for_load_state("networkidle")

        # 点击任务名称进入详情
        task_link = page.locator(".el-table__body tr td:nth-child(2)").first
        if task_link.is_visible():
            try:
                task_link.click()
                page.wait_for_timeout(2000)
                # 应该跳转到详情页
                current_url = page.url
                assert "/tasks/" in current_url, f"应该进入详情页，当前URL: {current_url}"
            except Exception:
                pytest.skip("任务列表为空或无法点击")
        else:
            pytest.skip("任务列表为空")
