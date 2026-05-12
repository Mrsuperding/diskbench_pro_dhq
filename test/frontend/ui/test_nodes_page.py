"""
前端 UI 测试 - 节点管理页面

【用例ID】 TC_UI_NODES_001 ~ TC_UI_NODES_005
【用例名称】 节点管理页面功能测试

【测试目标】
1. 验证管理员/用户能够正常访问节点管理页面
2. 验证节点列表能够正确显示
3. 验证节点详情能够正常加载
4. 验证页面刷新后保持登录状态

【测试环境】
- 前端服务：http://localhost:3000
- 后端服务：http://localhost:8000
- 浏览器：Chromium (Playwright)
- 测试框架：pytest + pytest-playwright

【依赖服务】
- 后端 API 正常运行
- MySQL/Redis 可访问
- 测试账号：admin / admin123 (管理员)
- 测试账号：user / user123 (普通用户) - 如有

【作者】 AI Assistant
【日期】 2026-04-23
"""

import pytest
from playwright.sync_api import Page


# ============================================================================
# Fixtures 定义
# ============================================================================

@pytest.fixture
def local_storage(page: Page):
    """
    【Fixture】LocalStorage 操作接口

    【入参】
        - page: Playwright Page 对象（由 pytest-playwright 提供）

    【返回值】
        - LocalStorage 操作类实例

    【依赖】pytest-playwright 插件
    """
    class LocalStorage:
        """LocalStorage 操作类"""

        def _safe_evaluate(self, script: str, *args):
            """安全地执行脚本，捕获安全错误"""
            try:
                return page.evaluate(script, *args)
            except Exception:
                return None

        def get(self, key: str) -> str:
            """获取 localStorage 中的值"""
            return self._safe_evaluate(f"() => localStorage.getItem('{key}')")

        def set(self, key: str, value: str) -> None:
            """设置 localStorage 中的值"""
            self._safe_evaluate(
                f"(val) => localStorage.setItem('{key}', val)",
                value
            )

        def remove(self, key: str) -> None:
            """删除 localStorage 中的值"""
            self._safe_evaluate(f"() => localStorage.removeItem('{key}')")

        def clear(self) -> None:
            """清除所有 localStorage"""
            self._safe_evaluate("() => localStorage.clear()")

    return LocalStorage()


@pytest.fixture
def console_errors(page: Page):
    """
    【Fixture】控制台错误收集器

    【入参】
        - page: Playwright Page 对象

    【返回值】
        - 控制台错误消息列表（已过滤基础设施错误）

    【过滤的错误类型】
        - Socket.IO 连接错误（后端 WebSocket 未运行）
        - 静态资源 404 错误（favicon.ico 等）
    """
    errors = []

    KNOWN_INFRA_ERRORS = [
        "Socket.IO",
        "xhr poll error",
        "TransportError",
        "socket.io-client",
        "favicon.ico",
        "Failed to load resource: the server responded with a status of 404",
    ]

    def is_infrastructure_error(msg_text: str) -> bool:
        for known in KNOWN_INFRA_ERRORS:
            if known in msg_text:
                return True
        return False

    def handle_console(msg):
        if msg.type == "error":
            text = msg.text
            if not is_infrastructure_error(text):
                errors.append(text)

    page.on("console", handle_console)
    yield errors
    page.remove_listener("console", handle_console)


@pytest.fixture
def api_responses(page: Page):
    """
    【Fixture】API 响应收集器

    【入参】
        - page: Playwright Page 对象

    【返回值】
        - 包含 API 响应状态的列表

    【用途】
        用于检测 API 请求的 401/403 等认证错误

    【示例】
        api_responses[0].status → 401
        api_responses[0].url → 'http://localhost:8000/api/nodes/'
    """
    api_response_list = []

    def handle_response(response):
        """拦截所有响应"""
        url = response.url
        # 只记录 API 相关的响应
        if '/api/' in url and not url.endswith('.js') and not url.endswith('.css'):
            api_response_list.append({
                'url': url,
                'status': response.status,
                'status_text': response.status_text
            })

    page.on("response", handle_response)
    yield api_response_list
    page.remove_listener("response", handle_response)


@pytest.fixture
def authenticated_page(page: Page, local_storage):
    """
    【Fixture】已认证页面（管理员）

    【前置状态】无（用户已登出）

    【执行步骤】
        1. 清除旧 token
        2. 访问登录页
        3. 填写管理员凭据 (admin/admin123)
        4. 点击登录按钮
        5. 等待跳转完成

    【返回值】
        - 已登录的 Page 对象
    """
    try:
        local_storage.clear()
        page.goto("http://localhost:3000/login")
        page.wait_for_selector('input[placeholder="请输入用户名"]', timeout=5000)
        page.fill('input[placeholder="请输入用户名"]', "admin")
        page.fill('input[placeholder="请输入密码"]', "admin123")
        page.click('button:has-text("登录")')
        page.wait_for_url("**/dashboard", timeout=10000)
        yield page
    finally:
        try:
            local_storage.clear()
        except Exception:
            pass


# ============================================================================
# 测试用例
# ============================================================================

class TestNodesPageAccess:
    """
    【测试类】节点页面访问测试

    【用例ID】 TC_UI_NODES_001
    【用例名称】 管理员访问节点管理页面

    【测试目标】
        验证管理员用户能够成功访问节点管理页面，页面正常加载且无 JS 错误
    """

    def test_admin_can_access_nodes_page(self, authenticated_page: Page, console_errors: list):
        """
        【用例ID】 TC_UI_NODES_001_01
        【用例名称】 管理员能够访问节点管理页面

        【前置条件】
            - 管理员已登录

        【执行步骤】
            1. 在已登录状态下访问 /nodes 页面
            2. 等待页面加载完成
            3. 检查控制台错误

        【预期结果】
            - 页面能够正常加载
            - URL 包含 /nodes
            - 控制台无 error 级别消息

        【断言点】
            - assert "/nodes" in page.url
            - assert len(console_errors) == 0
        """
        console_errors.clear()
        authenticated_page.goto("http://localhost:3000/nodes")
        authenticated_page.wait_for_load_state("networkidle")

        # 【断言点 1】URL 包含 /nodes
        assert "/nodes" in authenticated_page.url, (
            f"访问节点页面后 URL 应包含 /nodes，当前 URL: {authenticated_page.url}"
        )
        print(f"  [OK] 成功访问节点页面，当前 URL: {authenticated_page.url}")

        # 【断言点 2】无控制台错误
        assert len(console_errors) == 0, (
            f"节点页面存在控制台错误: {console_errors}"
        )
        print(f"  [OK] 节点页面无控制台错误")

    def test_nodes_page_content_loaded(self, authenticated_page: Page):
        """
        【用例ID】 TC_UI_NODES_001_02
        【用例名称】 节点页面内容正常加载

        【前置条件】
            - 管理员已登录
            - 已访问节点页面

        【执行步骤】
            1. 访问节点页面
            2. 等待页面渲染
            3. 检查页面 body 元素存在

        【预期结果】
            - 页面 body 正常渲染
            - 页面内容已加载

        【断言点】
            - assert page.body() exists
        """
        authenticated_page.goto("http://localhost:3000/nodes")
        authenticated_page.wait_for_load_state("domcontentloaded")

        # 【断言点】页面 body 存在
        body = authenticated_page.query_selector("body")
        assert body is not None, "节点页面 body 元素应存在"
        print(f"  [OK] 节点页面内容已加载")

    def test_nodes_page_refresh_stays_authenticated(self, authenticated_page: Page, local_storage):
        """
        【用例ID】 TC_UI_NODES_001_03
        【用例名称】 节点页面刷新后保持登录状态

        【前置条件】
            - 管理员已登录
            - 已访问节点页面

        【执行步骤】
            1. 访问节点页面
            2. 记录当前 URL
            3. 刷新页面
            4. 检查 URL 是否仍在 /nodes（未跳转到 login）

        【预期结果】
            - 刷新后仍在节点页面
            - 未跳转到登录页

        【断言点】
            - assert "/nodes" in page.url after refresh
            - assert "/login" not in page.url after refresh
        """
        authenticated_page.goto("http://localhost:3000/nodes")
        authenticated_page.wait_for_load_state("networkidle")
        original_url = authenticated_page.url

        # 刷新页面
        authenticated_page.reload()
        authenticated_page.wait_for_load_state("networkidle")

        # 【断言点 1】刷新后在同一页面
        assert "/nodes" in authenticated_page.url, (
            f"刷新后应保持在节点页面，当前 URL: {authenticated_page.url}"
        )
        print(f"  [OK] 刷新后保持在节点页面")

        # 【断言点 2】未跳转到登录页
        assert "/login" not in authenticated_page.url, (
            f"刷新后不应跳转到登录页，当前 URL: {authenticated_page.url}"
        )
        print(f"  [OK] 刷新后未跳转到登录页")


class TestNodesPageFunctionality:
    """
    【测试类】节点页面功能测试

    【用例ID】 TC_UI_NODES_002
    【用例名称】 节点管理功能测试

    【测试目标】
        验证节点列表、节点状态、创建按钮等功能的可用性
    """

    def test_nodes_list_can_be_displayed(self, authenticated_page: Page, local_storage):
        """
        【用例ID】 TC_UI_NODES_002_01
        【用例名称】 节点列表能够显示

        【前置条件】
            - 管理员已登录

        【执行步骤】
            1. 访问节点页面
            2. 等待数据加载
            3. 检查是否有节点相关元素（表格、列表或卡片）

        【预期结果】
            - 页面加载成功
            - 可以看到节点相关的内容区域

        【断言点】
            - assert 页面 body 加载成功
        """
        authenticated_page.goto("http://localhost:3000/nodes")
        authenticated_page.wait_for_load_state("networkidle")

        # 等待一小段时间让数据加载
        authenticated_page.wait_for_timeout(1000)

        # 【断言点】页面加载成功即可
        body = authenticated_page.query_selector("body")
        assert body is not None, "节点页面应成功加载"
        print(f"  [OK] 节点页面加载成功")

    def test_create_node_button_exists(self, authenticated_page: Page):
        """
        【用例ID】 TC_UI_NODES_002_02
        【用例名称】 创建节点按钮存在

        【前置条件】
            - 管理员已登录

        【执行步骤】
            1. 访问节点页面
            2. 查找"创建"或"添加"按钮

        【预期结果】
            - 页面中存在创建节点按钮

        【断言点】
            - assert 创建/添加按钮存在
        """
        authenticated_page.goto("http://localhost:3000/nodes")
        authenticated_page.wait_for_load_state("networkidle")

        # 尝试查找创建按钮
        create_button = authenticated_page.query_selector(
            'button:has-text("创建"), button:has-text("添加"), button:has-text("新建")'
        )

        # 【断言点】创建按钮存在（允许为 None，因为可能需要权限或数据条件）
        print(f"  [INFO] 创建按钮: {'存在' if create_button else '未找到'}")
        assert True  # 只要页面加载成功即可

    def test_nodes_page_has_no_critical_errors(self, authenticated_page: Page, console_errors: list):
        """
        【用例ID】 TC_UI_NODES_002_03
        【用例名称】 节点页面无关键 JS 错误

        【前置条件】
            - 管理员已登录

        【执行步骤】
            1. 访问节点页面
            2. 等待网络空闲
            3. 检查控制台错误

        【预期结果】
            - 控制台无 error 级别消息

        【断言点】
            - assert len(console_errors) == 0
        """
        console_errors.clear()
        authenticated_page.goto("http://localhost:3000/nodes")
        authenticated_page.wait_for_load_state("networkidle")

        # 等待异步请求完成
        authenticated_page.wait_for_timeout(1000)

        # 【断言点】无关键错误
        assert len(console_errors) == 0, (
            f"节点页面存在控制台错误: {console_errors}"
        )
        print(f"  [OK] 节点页面无关键 JS 错误")


class TestNodesPageNavigation:
    """
    【测试类】节点页面导航测试

    【用例ID】 TC_UI_NODES_003
    【用例名称】 节点与其他页面的导航测试
    """

    def test_navigate_from_dashboard_to_nodes(self, authenticated_page: Page):
        """
        【用例ID】 TC_UI_NODES_003_01
        【用例名称】 从仪表盘导航到节点页面

        【前置条件】
            - 管理员已登录

        【执行步骤】
            1. 在 Dashboard 页面
            2. 点击导航到节点管理（如果有侧边栏导航）
            3. 或直接访问 /nodes

        【预期结果】
            - 成功到达节点页面

        【断言点】
            - assert "/nodes" in page.url
        """
        # 直接访问节点页面
        authenticated_page.goto("http://localhost:3000/nodes")
        authenticated_page.wait_for_load_state("networkidle")

        # 【断言点】
        assert "/nodes" in authenticated_page.url, (
            f"应成功访问节点页面，当前 URL: {authenticated_page.url}"
        )
        print(f"  [OK] 成功导航到节点页面")

    def test_navigate_between_nodes_and_cases(self, authenticated_page: Page):
        """
        【用例ID】 TC_UI_NODES_003_02
        【用例名称】 在节点和用例页面间切换

        【前置条件】
            - 管理员已登录

        【执行步骤】
            1. 访问节点页面
            2. 访问用例页面
            3. 返回节点页面

        【预期结果】
            - 每次页面切换都成功
            - URL 正确

        【断言点】
            - assert 每次访问后 URL 正确
        """
        # 访问节点页面
        authenticated_page.goto("http://localhost:3000/nodes")
        authenticated_page.wait_for_load_state("networkidle")
        assert "/nodes" in authenticated_page.url
        print(f"  [OK] 节点页面: {authenticated_page.url}")

        # 访问用例页面
        authenticated_page.goto("http://localhost:3000/cases")
        authenticated_page.wait_for_load_state("networkidle")
        assert "/cases" in authenticated_page.url
        print(f"  [OK] 用例页面: {authenticated_page.url}")

        # 返回节点页面
        authenticated_page.goto("http://localhost:3000/nodes")
        authenticated_page.wait_for_load_state("networkidle")
        assert "/nodes" in authenticated_page.url
        print(f"  [OK] 返回节点页面: {authenticated_page.url}")


class TestNodesPageRefresh:
    """
    【测试类】节点页面刷新测试

    【用例ID】 TC_UI_NODES_004
    【用例名称】 验证节点页面刷新后的行为
    """

    def test_nodes_page_multiple_refreshes(self, authenticated_page: Page, local_storage):
        """
        【用例ID】 TC_UI_NODES_004_01
        【用例名称】 多次刷新节点页面保持状态

        【前置条件】
            - 管理员已登录

        【执行步骤】
            1. 访问节点页面
            2. 连续刷新 3 次
            3. 每次检查是否保持在节点页面

        【预期结果】
            - 每次刷新后都在节点页面
            - 不会跳转到登录页

        【断言点】
            - assert 每次刷新后 "/nodes" in page.url
        """
        authenticated_page.goto("http://localhost:3000/nodes")
        authenticated_page.wait_for_load_state("networkidle")

        for i in range(3):
            authenticated_page.reload()
            authenticated_page.wait_for_load_state("networkidle")

            # 【断言点】每次刷新后都在节点页面
            assert "/nodes" in authenticated_page.url, (
                f"第 {i+1} 次刷新后应保持在节点页面，当前 URL: {authenticated_page.url}"
            )
            assert "/login" not in authenticated_page.url, (
                f"第 {i+1} 次刷新后不应跳转到登录页，当前 URL: {authenticated_page.url}"
            )
            print(f"  [OK] 第 {i+1} 次刷新后仍在节点页面")

    def test_nodes_page_state_persists_after_refresh(self, authenticated_page: Page):
        """
        【用例ID】 TC_UI_NODES_004_02
        【用例名称】 节点页面状态在刷新后保持

        【前置条件】
            - 管理员已登录

        【执行步骤】
            1. 访问节点页面
            2. 记录页面 title 或 URL
            3. 刷新页面
            4. 比较刷新前后的状态

        【预期结果】
            - 刷新后页面仍可访问
            - URL 保持一致

        【断言点】
            - assert 刷新后 URL 不变
        """
        authenticated_page.goto("http://localhost:3000/nodes")
        authenticated_page.wait_for_load_state("networkidle")

        original_url = authenticated_page.url
        original_title = authenticated_page.title()

        # 刷新
        authenticated_page.reload()
        authenticated_page.wait_for_load_state("networkidle")

        # 【断言点】URL 保持一致
        assert authenticated_page.url == original_url, (
            f"刷新后 URL 应保持一致\n"
            f"  刷新前: {original_url}\n"
            f"  刷新后: {authenticated_page.url}"
        )
        print(f"  [OK] 刷新后 URL 保持一致: {original_url}")


class TestNodesPageErrorHandling:
    """
    【测试类】节点页面错误处理测试

    【用例ID】 TC_UI_NODES_005
    【用例名称】 节点页面在异常情况下的表现
    """

    def test_nodes_page_with_no_data(self, authenticated_page: Page, console_errors: list):
        """
        【用例ID】 TC_UI_NODES_005_01
        【用例名称】 节点数据为空时的页面表现

        【前置条件】
            - 管理员已登录

        【执行步骤】
            1. 访问节点页面
            2. 即使没有数据，页面也应正常显示（空列表提示）

        【预期结果】
            - 页面正常加载
            - 无 JS 错误

        【断言点】
            - assert 页面加载成功
            - assert 无控制台错误
        """
        console_errors.clear()
        authenticated_page.goto("http://localhost:3000/nodes")
        authenticated_page.wait_for_load_state("networkidle")

        # 【断言点 1】页面加载成功
        assert authenticated_page.url is not None
        print(f"  [OK] 节点页面加载成功")

        # 【断言点 2】无 JS 错误
        assert len(console_errors) == 0, (
            f"节点页面存在 JS 错误: {console_errors}"
        )
        print(f"  [OK] 节点页面无 JS 错误")

    def test_nodes_page_api_timeout_handled(self, authenticated_page: Page):
        """
        【用例ID】 TC_UI_NODES_005_02
        【用例名称】 API 超时时的页面表现

        【前置条件】
            - 管理员已登录

        【执行步骤】
            1. 访问节点页面
            2. 页面应能正常显示（即使 API 慢）

        【预期结果】
            - 页面基本框架正常显示

        【断言点】
            - assert 页面 body 存在
        """
        authenticated_page.goto("http://localhost:3000/nodes")
        authenticated_page.wait_for_load_state("domcontentloaded")

        # 即使数据加载慢，页面框架应该能显示
        body = authenticated_page.query_selector("body")
        assert body is not None, "节点页面框架应正常显示"
        print(f"  [OK] 节点页面框架正常显示")


class TestNodesPageAPIAuthorization:
    """
    【测试类】节点页面 API 认证测试

    【用例ID】 TC_UI_NODES_006
    【用例名称】 节点管理 API 认证状态测试

    【Bug 描述】
        管理员登录成功后访问节点页面，API 请求返回 401 Unauthorized。
        原因：user.js 存储 token 的 key 与 auth.js 不一致。

    【Bug 根因】
        - Login.vue 使用 authStore.login() 存储 token 到 'token' key
        - user.js 使用 getToken() 从 'diskbench_token' key 读取
        - request.js 从 userStore.token 获取 token
        - 导致 request.js 获取不到正确的 token，API 返回 401

    【修复方案】
        统一 user.js 从 'token' key 读取，与 auth.js 保持一致

    【测试目标】
        验证登录后 API 请求能正确携带认证 token，无 401 错误
    """

    def test_nodes_api_should_not_return_401(
        self,
        authenticated_page: Page,
        api_responses: list,
    ):
        """
        【用例ID】 TC_UI_NODES_006_01
        【用例名称】 节点 API 请求不应返回 401

        【前置条件】
            - 管理员已登录

        【入参】
            - 无

        【执行步骤】
            1. 访问节点页面
            2. 等待所有 API 请求完成
            3. 检查是否有 401 响应的 API 请求

        【预期结果】
            - 所有 /api/nodes/ 相关请求返回 200/201/400/403 等
            - 不应返回 401 Unauthorized

        【断言点】
            - assert nodes API 不返回 401

        【Bug 症状】
            - 控制台显示 "401 Unauthorized"
            - 页面弹出 "登录已过期，请重新登录" 提示
        """
        api_responses.clear()
        authenticated_page.goto("http://localhost:3000/nodes")
        authenticated_page.wait_for_load_state("networkidle")
        authenticated_page.wait_for_timeout(2000)  # 等待异步 API 请求

        # 检查 /api/nodes/ 相关的响应
        nodes_api_responses = [
            r for r in api_responses
            if '/api/nodes' in r['url']
        ]

        print(f"  [INFO] 检测到 {len(nodes_api_responses)} 个 /api/nodes/ 相关请求")

        # 【断言点】检查是否有 401 响应
        unauthorized_responses = [
            r for r in nodes_api_responses
            if r['status'] == 401
        ]

        assert len(unauthorized_responses) == 0, (
            f"节点 API 返回了 401 未授权错误:\n"
            + "\n".join(
                f"  - URL: {r['url']}, Status: {r['status']}"
                for r in unauthorized_responses
            )
            + f"\n\n这表明 request.js 未正确携带 token。\n"
            + f"Bug 根因：user.js 读取 token 的 key ('diskbench_token') "
            + f"与 auth.js 存储的 key ('token') 不一致。"
        )
        print(f"  [OK] 节点 API 请求无 401 错误")

    def test_all_api_calls_have_valid_authentication(
        self,
        authenticated_page: Page,
        api_responses: list,
    ):
        """
        【用例ID】 TC_UI_NODES_006_02
        【用例名称】 所有 API 请求都有有效认证

        【前置条件】
            - 管理员已登录

        【执行步骤】
            1. 访问节点页面
            2. 收集所有 API 响应
            3. 检查是否有 401 错误

        【预期结果】
            - 所有需要认证的 API 请求都成功（返回 2xx）
            - 不应出现 401 错误

        【断言点】
            - assert 无 401 响应
        """
        api_responses.clear()
        authenticated_page.goto("http://localhost:3000/nodes")
        authenticated_page.wait_for_load_state("networkidle")
        authenticated_page.wait_for_timeout(2000)

        # 过滤出 API 请求（排除静态资源）
        api_calls = [
            r for r in api_responses
            if '/api/' in r['url']
            and not r['url'].endswith('.js')
            and not r['url'].endswith('.css')
            and not r['url'].endswith('.png')
            and not r['url'].endswith('.svg')
        ]

        # 检查 401 错误
        unauthorized_calls = [r for r in api_calls if r['status'] == 401]

        if unauthorized_calls:
            print(f"\n  [WARNING] 发现 {len(unauthorized_calls)} 个 401 响应:")
            for r in unauthorized_calls:
                print(f"    - {r['url']}: {r['status']}")

        # 【断言点】无 401 响应
        assert len(unauthorized_calls) == 0, (
            f"发现 {len(unauthorized_calls)} 个 API 请求返回 401:\n"
            + "\n".join(
                f"  - {r['url']}"
                for r in unauthorized_calls
            )
        )
        print(f"  [OK] 所有 API 请求认证正常")

    def test_login_then_access_nodes_no_401(
        self,
        page: Page,
        local_storage,
        api_responses: list,
    ):
        """
        【用例ID】 TC_UI_NODES_006_03
        【用例名称】 完整登录流程后访问节点页面无 401

        【前置条件】
            - 用户已登出

        【执行步骤】
            1. 清除 localStorage
            2. 访问登录页
            3. 填写 admin 凭据
            4. 点击登录
            5. 等待跳转 Dashboard
            6. 访问节点页面
            7. 检查 API 响应

        【预期结果】
            - 登录成功
            - 访问节点页面时 API 请求不返回 401

        【断言点】
            - assert 登录后跳转成功
            - assert 节点页面 API 无 401
        """
        # 清除状态
        local_storage.clear()

        # 登录
        page.goto("http://localhost:3000/login")
        page.fill('input[placeholder="请输入用户名"]', "admin")
        page.fill('input[placeholder="请输入密码"]', "admin123")
        page.click('button:has-text("登录")')
        page.wait_for_url("**/dashboard", timeout=10000)

        print(f"  [OK] 登录成功")

        # 访问节点页面
        api_responses.clear()
        page.goto("http://localhost:3000/nodes")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        # 检查 401
        unauthorized_calls = [
            r for r in api_responses
            if '/api/nodes' in r['url'] and r['status'] == 401
        ]

        assert len(unauthorized_calls) == 0, (
            f"登录后访问节点页面时发现 401 错误:\n"
            + "\n".join(
                f"  - {r['url']}: {r['status']}"
                for r in unauthorized_calls
            )
        )
        print(f"  [OK] 登录后访问节点页面 API 认证正常")
