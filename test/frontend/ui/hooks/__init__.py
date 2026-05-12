"""
Hooks Package
=============
Pytest hooks 扩展模块

导入后自动注册所有 hooks
"""
from hooks.pytest_hooks import (
    pytest_sessionstart,
    pytest_sessionfinish,
    pytest_runtest_makereport,
    pytest_configure,
)

__all__ = [
    'pytest_sessionstart',
    'pytest_sessionfinish',
    'pytest_runtest_makereport',
    'pytest_configure',
]
