"""
Backend Error Logger - 后端错误日志收集器
==========================================
收集和存储后端错误信息用于分析

用法：
    from test.utils.backend_error_logger import backend_error_logger

    # 在测试中收集错误
    @pytest.fixture
    def backend_error_tracker():
        backend_error_logger.clear()
        yield backend_error_logger
        backend_error_logger.save_report()

    # 或者在测试后手动调用
    backend_error_logger.generate_error_report()
"""
import json
import os
import traceback
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict


class BackendErrorLogger:
    """后端错误日志收集器"""

    def __init__(self, log_dir: str = "test-results/backend_errors"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.errors = []
        self.warnings = []
        self.api_calls = []
        self._lock = threading.Lock()

        # 错误类型统计
        self.error_counts = defaultdict(int)
        self.error_by_endpoint = defaultdict(list)

    def clear(self):
        """清空所有收集的数据"""
        with self._lock:
            self.errors.clear()
            self.warnings.clear()
            self.api_calls.clear()
            self.error_counts.clear()
            self.error_by_endpoint.clear()

    def log_error(
        self,
        error_type: str,
        message: str,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None,
        request_id: Optional[str] = None,
        detail: Optional[Any] = None,
        stack_trace: Optional[str] = None
    ):
        """记录错误"""
        with self._lock:
            error_entry = {
                "timestamp": datetime.now().isoformat(),
                "error_type": error_type,
                "message": message,
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "request_id": request_id,
                "detail": detail,
                "stack_trace": stack_trace or traceback.format_exc()
            }
            self.errors.append(error_entry)

            # 统计
            self.error_counts[error_type] += 1
            if endpoint:
                self.error_by_endpoint[endpoint].append(error_entry)

    def log_warning(self, message: str, context: Optional[Dict] = None):
        """记录警告"""
        with self._lock:
            warning_entry = {
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "context": context or {}
            }
            self.warnings.append(warning_entry)

    def log_api_call(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        request_data: Optional[Dict] = None,
        response_data: Optional[Dict] = None,
        duration_ms: Optional[float] = None
    ):
        """记录 API 调用（成功和失败）"""
        with self._lock:
            call_entry = {
                "timestamp": datetime.now().isoformat(),
                "method": method,
                "endpoint": endpoint,
                "status_code": status_code,
                "request_data": request_data,
                "response_data": response_data,
                "duration_ms": duration_ms,
                "is_error": status_code >= 400
            }
            self.api_calls.append(call_entry)

    def log_validation_error(
        self,
        endpoint: str,
        method: str,
        errors: List[Dict],
        request_data: Optional[Dict] = None
    ):
        """记录验证错误"""
        self.log_error(
            error_type="ValidationError",
            message="请求参数校验失败",
            endpoint=endpoint,
            method=method,
            status_code=422,
            detail=errors,
            request_id=None
        )

    def log_database_error(
        self,
        error_type: str,
        message: str,
        query: Optional[str] = None,
        detail: Optional[str] = None
    ):
        """记录数据库错误"""
        self.log_error(
            error_type=f"DatabaseError_{error_type}",
            message=message,
            detail={"query": query, "original_error": detail},
            stack_trace=traceback.format_exc()
        )

    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        with self._lock:
            return {
                "total_errors": len(self.errors),
                "total_warnings": len(self.warnings),
                "total_api_calls": len(self.api_calls),
                "error_count_by_type": dict(self.error_counts),
                "error_count_by_endpoint": {
                    k: len(v) for k, v in self.error_by_endpoint.items()
                },
                "most_common_errors": self._get_most_common_errors(5)
            }

    def _get_most_common_errors(self, limit: int) -> List[Dict]:
        """获取最常见的错误"""
        sorted_errors = sorted(
            self.error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        return [
            {"error_type": et, "count": count}
            for et, count in sorted_errors
        ]

    def generate_error_report(self, output_file: Optional[str] = None) -> str:
        """生成错误报告"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.log_dir / f"error_report_{timestamp}.json"

        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": self.get_error_summary(),
            "errors": self.errors,
            "warnings": self.warnings,
            "api_calls": self.api_calls
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return str(output_file)

    def generate_markdown_report(self, output_file: Optional[str] = None) -> str:
        """生成 Markdown 格式的错误报告"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.log_dir / f"error_report_{timestamp}.md"

        summary = self.get_error_summary()

        md = []
        md.append("# Backend Error Report")
        md.append(f"\n**Generated:** {datetime.now().isoformat()}\n")

        md.append("## Summary")
        md.append(f"- Total Errors: {summary['total_errors']}")
        md.append(f"- Total Warnings: {summary['total_warnings']}")
        md.append(f"- Total API Calls: {summary['total_api_calls']}")

        md.append("\n## Error Count by Type")
        for et, count in summary['error_count_by_type'].items():
            md.append(f"- {et}: {count}")

        md.append("\n## Error Count by Endpoint")
        for endpoint, errors in summary['error_count_by_endpoint'].items():
            md.append(f"- {endpoint}: {len(errors)}")

        if summary['most_common_errors']:
            md.append("\n## Most Common Errors")
            for err in summary['most_common_errors']:
                md.append(f"- {err['error_type']}: {err['count']} occurrences")

        if self.errors:
            md.append("\n## Error Details")
            for i, err in enumerate(self.errors, 1):
                md.append(f"\n### Error {i}: {err['error_type']}")
                md.append(f"- **Message:** {err['message']}")
                md.append(f"- **Time:** {err['timestamp']}")
                if err['endpoint']:
                    md.append(f"- **Endpoint:** {err['method']} {err['endpoint']}")
                if err['status_code']:
                    md.append(f"- **Status:** {err['status_code']}")
                if err['request_id']:
                    md.append(f"- **Request ID:** {err['request_id']}")
                if err['detail']:
                    md.append(f"- **Detail:** {json.dumps(err['detail'], ensure_ascii=False)}")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(md))

        return str(output_file)

    def save_report(self):
        """保存报告（JSON 格式）"""
        return self.generate_error_report()

    def analyze_error_trends(self) -> Dict[str, Any]:
        """分析错误趋势"""
        if not self.api_calls:
            return {}

        error_calls = [c for c in self.api_calls if c["is_error"]]
        success_calls = [c for c in self.api_calls if not c["is_error"]]

        return {
            "total_requests": len(self.api_calls),
            "success_rate": len(success_calls) / len(self.api_calls) if self.api_calls else 0,
            "error_rate": len(error_calls) / len(self.api_calls) if self.api_calls else 0,
            "error_status_codes": self._count_status_codes(error_calls),
            "slow_endpoints": self._get_slow_endpoints(),
            "endpoints_with_errors": list(self.error_by_endpoint.keys())
        }

    def _count_status_codes(self, calls: List[Dict]) -> Dict[int, int]:
        """统计状态码"""
        counts = defaultdict(int)
        for call in calls:
            counts[call["status_code"]] += 1
        return dict(counts)

    def _get_slow_endpoints(self) -> List[Dict]:
        """获取响应慢的端点"""
        endpoint_times = defaultdict(list)
        for call in self.api_calls:
            if call.get("duration_ms") and call["endpoint"]:
                endpoint_times[call["endpoint"]].append(call["duration_ms"])

        slow = []
        for endpoint, times in endpoint_times.items():
            avg = sum(times) / len(times)
            if avg > 1000:  # 超过 1 秒
                slow.append({"endpoint": endpoint, "avg_ms": round(avg, 2), "count": len(times)})

        return sorted(slow, key=lambda x: x["avg_ms"], reverse=True)


# 全局实例
backend_error_logger = BackendErrorLogger()


class ErrorCollectionPlugin:
    """错误收集插件（用于 pytest）"""

    def __init__(self):
        self.logger = backend_error_logger

    def pytest_runtest_makereport(self, item, call):
        """在测试报告阶段收集错误"""
        if call.excinfo is not None:
            # 测试失败，收集错误信息
            self.logger.log_error(
                error_type="TestFailure",
                message=str(call.excinfo.value),
                detail={
                    "test_name": item.name,
                    "test_module": item.module.__name__,
                    "stage": call.when
                }
            )

    def pytest_sessionfinish(self, session, exitstatus):
        """测试会话结束，生成报告"""
        if exitstatus != 0:
            report_file = self.logger.generate_markdown_report()
            print(f"\n[BackendErrorLogger] Error report saved to: {report_file}")


# 使用示例和工具函数
def create_error_report_for_test(test_name: str, errors: List[Dict]) -> str:
    """为单个测试创建错误报告"""
    report = {
        "test_name": test_name,
        "timestamp": datetime.now().isoformat(),
        "errors": errors
    }

    report_dir = Path("test-results/backend_errors")
    report_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{test_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_file = report_dir / filename

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return str(report_file)


# 辅助函数：从 API 响应中提取错误
def extract_error_from_response(response_data: Dict) -> Optional[Dict]:
    """从 API 响应中提取错误信息"""
    if "code" in response_data and response_data["code"] >= 400:
        return {
            "error_type": "APIError",
            "code": response_data.get("code"),
            "message": response_data.get("message"),
            "detail": response_data.get("detail"),
            "request_id": response_data.get("request_id")
        }
    return None


# 辅助函数：分析验证错误
def analyze_validation_errors(errors: List[Dict]) -> Dict[str, Any]:
    """分析验证错误"""
    field_errors = defaultdict(list)
    for err in errors:
        field = ".".join(str(p) for p in err.get("loc", []))
        field_errors[field].append({
            "type": err.get("type"),
            "message": err.get("msg")
        })

    return {
        "total_errors": len(errors),
        "fields_with_errors": list(field_errors.keys()),
        "field_error_details": dict(field_errors)
    }