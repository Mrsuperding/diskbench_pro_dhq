# Page Objects Package
"""
Page Object Model (POM) for DiskBench Pro UI Testing

提供页面对象封装：
- base: 基础类 (BasePage, AutoWait, Component)
- auth: 认证相关页面 (LoginPage)
- dashboard: 概览页面
- nodes: 节点管理页面
- cases: 用例管理页面
- tasks: 任务管理页面
- schedules: 定时调度页面
"""

# Base classes
from page_objects.base.base_page import BasePage, AutoWait
from page_objects.base.component import Component

# Auth pages
from page_objects.auth.login_page import LoginPage

# Dashboard page
from page_objects.dashboard.dashboard_page import DashboardPage

# Nodes pages
from page_objects.nodes.nodes_list_page import NodesListPage

# Cases pages
from page_objects.cases.cases_list_page import CasesListPage

# Tasks pages
from page_objects.tasks.tasks_list_page import TasksListPage
from page_objects.tasks.task_form_page import TaskFormPage

# Schedules pages
from page_objects.schedules.schedules_list_page import SchedulesListPage

__all__ = [
    # Base
    'BasePage',
    'AutoWait',
    'Component',
    # Auth
    'LoginPage',
    # Dashboard
    'DashboardPage',
    # Nodes
    'NodesListPage',
    # Cases
    'CasesListPage',
    # Tasks
    'TasksListPage',
    # Schedules
    'SchedulesListPage',
]
