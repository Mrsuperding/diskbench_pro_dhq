"""
Test Utilities Package
=====================
提供错误收集和分析工具

使用示例：
    from page_objects.tests.test_utils import (
        backend_error_logger,
        frontend_error_collector,
        combined_analyzer
    )
"""
from page_objects.tests.test_utils.backend_error_logger import (
    BackendErrorLogger,
    backend_error_logger,
    ErrorCollectionPlugin,
    create_error_report_for_test,
    extract_error_from_response,
    analyze_validation_errors
)

from page_objects.tests.test_utils.frontend_error_collector import (
    FrontendErrorCollector,
    FrontendErrorCollectorFixture,
    frontend_error_collector,
    create_frontend_error_report
)

from page_objects.tests.test_utils.combined_error_analyzer import (
    CombinedErrorAnalyzer,
    CombinedErrorAnalyzer,
    TestErrorCollector,
    combined_analyzer,
    quick_analysis
)

__all__ = [
    # Backend error logger
    'BackendErrorLogger',
    'backend_error_logger',
    'ErrorCollectionPlugin',
    'create_error_report_for_test',
    'extract_error_from_response',
    'analyze_validation_errors',
    # Frontend error collector
    'FrontendErrorCollector',
    'FrontendErrorCollectorFixture',
    'frontend_error_collector',
    'create_frontend_error_report',
    # Combined analyzer
    'CombinedErrorAnalyzer',
    'TestErrorCollector',
    'combined_analyzer',
    'quick_analysis'
]