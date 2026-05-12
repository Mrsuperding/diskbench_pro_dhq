"""
Frontend Error Collector - 前端错误收集器
==========================================
收集前端控制台错误和 API 响应错误

用法：
    from test_utils.frontend_error_collector import frontend_error_collector

    @pytest.fixture
    def frontend_errors(page):
        collector = FrontendErrorCollector(page)
        yield collector
        collector.generate_report()
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from collections import defaultdict


@dataclass
class ConsoleError:
    """控制台错误"""
    timestamp: str
    type: str
    text: str
    location: str
    stack_trace: Optional[str] = None


@dataclass
class NetworkError:
    """网络错误"""
    timestamp: str
    url: str
    method: str
    status: int
    status_text: str
    request_body: Optional[str] = None
    response_body: Optional[str] = None
    duration_ms: Optional[float] = None


@dataclass
class PageError:
    """页面错误（未捕获异常）"""
    timestamp: str
    message: str
    filename: str
    lineno: int
    colno: int
    stack: Optional[str] = None


class FrontendErrorCollector:
    """前端错误收集器"""

    def __init__(self, page=None):
        self.page = page
        self.console_errors: List[ConsoleError] = []
        self.network_errors: List[NetworkError] = []
        self.page_errors: List[PageError] = []
        self.api_responses: List[Dict] = []
        self.js_errors: List[Dict] = []
        self._is_recording = False
        self.log_dir = Path("test-results/frontend_errors")
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def start_recording(self):
        """开始记录错误"""
        if self.page and not self._is_recording:
            self._is_recording = True

            # 监听控制台错误
            self._console_handler = lambda msg: self._handle_console(msg)
            self.page.on("console", self._console_handler)

            # 监听请求失败
            self._requestfailed_handler = lambda req, err: self._handle_request_failed(req, err)
            self.page.on("requestfailed", self._requestfailed_handler)

            # 监听响应
            self._response_handler = lambda res: self._handle_response(res)
            self.page.on("response", self._response_handler)

    def stop_recording(self):
        """停止记录错误"""
        if self.page and self._is_recording:
            self._is_recording = False
            self.page.remove_listener("console", self._console_handler)
            self.page.remove_listener("requestfailed", self._requestfailed_handler)
            self.page.remove_listener("response", self._response_handler)

    def _handle_console(self, msg):
        """处理控制台消息"""
        if msg.type == "error":
            location = msg.location
            self.console_errors.append(ConsoleError(
                timestamp=datetime.now().isoformat(),
                type="console_error",
                text=msg.text,
                location=f"{location.get('url', '')}:{location.get('lineNumber', 0)}:{location.get('columnNumber', 0)}",
                stack_trace=msg.text if "Error" in msg.text else None
            ))

    def _handle_request_failed(self, request, failure):
        """处理请求失败"""
        self.network_errors.append(NetworkError(
            timestamp=datetime.now().isoformat(),
            url=request.url,
            method=request.method,
            status=0,
            status_text=str(failure),
        ))

    def _handle_response(self, response):
        """处理响应"""
        if "/api/" in response.url:
            self.api_responses.append({
                "timestamp": datetime.now().isoformat(),
                "url": response.url,
                "status": response.status,
                "method": response.request.method
            })

            # 检查 4xx/5xx 错误
            if response.status >= 400:
                try:
                    body = response.text()
                    self.network_errors.append(NetworkError(
                        timestamp=datetime.now().isoformat(),
                        url=response.url,
                        method=response.request.method,
                        status=response.status,
                        status_text=response.status_text,
                        response_body=body[:1000] if body else None
                    ))
                except Exception:
                    pass

    def clear(self):
        """清空所有收集的数据"""
        self.console_errors.clear()
        self.network_errors.clear()
        self.page_errors.clear()
        self.api_responses.clear()
        self.js_errors.clear()

    def get_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        # 过滤基础设施错误（Socket.IO, 网络重试等）
        infra_errors = self._filter_infrastructure_errors()

        return {
            "total_console_errors": len(self.console_errors),
            "total_network_errors": len(self.network_errors),
            "total_page_errors": len(self.page_errors),
            "total_api_responses": len(self.api_responses),
            "application_errors": len(infra_errors),
            "status_code_distribution": self._count_status_codes(),
            "error_urls": list(set(e.url for e in self.network_errors))
        }

    def _filter_infrastructure_errors(self) -> List[ConsoleError]:
        """过滤基础设施相关的错误"""
        infra_keywords = [
            "Socket.IO", "xhr poll error", "TransportError", "socket.io-client",
            "favicon", "favicon.ico", "favicon.svg",
            "Failed to load resource: the server responded with a status of 404",
            "Failed to load resource: the server responded with a status of 401",
            "Failed to load resource: the server responded with a status of 503",
            "net::ERR_CONNECTION_REFUSED", "net::ERR_CONNECTION_RESET"
        ]

        filtered = []
        for err in self.console_errors:
            is_infra = any(kw in err.text for kw in infra_keywords)
            if not is_infra:
                filtered.append(err)
        return filtered

    def _count_status_codes(self) -> Dict[int, int]:
        """统计状态码分布"""
        codes = defaultdict(int)
        for resp in self.api_responses:
            codes[resp["status"]] += 1
        return dict(codes)

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """生成前端错误报告"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.log_dir / f"frontend_errors_{timestamp}.json"

        # 过滤后的应用错误
        app_errors = self._filter_infrastructure_errors()

        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": self.get_summary(),
            "application_errors": [asdict(e) for e in app_errors],
            "all_console_errors": [asdict(e) for e in self.console_errors],
            "network_errors": [asdict(e) for e in self.network_errors],
            "api_responses": self.api_responses
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return str(output_file)

    def generate_markdown_report(self, output_file: Optional[str] = None) -> str:
        """生成 Markdown 格式的前端错误报告"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.log_dir / f"frontend_errors_{timestamp}.md"

        summary = self.get_summary()
        app_errors = self._filter_infrastructure_errors()

        md = []
        md.append("# Frontend Error Report")
        md.append(f"\n**Generated:** {datetime.now().isoformat()}\n")

        md.append("## Summary")
        md.append(f"- Total Console Errors: {summary['total_console_errors']}")
        md.append(f"- Total Network Errors: {summary['total_network_errors']}")
        md.append(f"- Total API Responses: {summary['total_api_responses']}")
        md.append(f"- Application Errors (non-infrastructure): {len(app_errors)}")

        if summary['status_code_distribution']:
            md.append("\n## Status Code Distribution")
            for code, count in sorted(summary['status_code_distribution'].items()):
                md.append(f"- {code}: {count}")

        if app_errors:
            md.append("\n## Application Errors (需要关注)")
            for i, err in enumerate(app_errors, 1):
                md.append(f"\n### {i}. {err.text}")
                md.append(f"   - Location: {err.location}")
                md.append(f"   - Time: {err.timestamp}")

        if self.network_errors:
            md.append("\n## Network Errors")
            for i, err in enumerate(self.network_errors[:10], 1):
                md.append(f"\n### {i}. {err.status} {err.method} {err.url}")
                md.append(f"   - Status: {err.status_text}")
                if err.response_body:
                    md.append(f"   - Response: {err.response_body[:200]}")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(md))

        return str(output_file)

    def get_error_urls(self) -> List[str]:
        """获取所有报错的 URL"""
        return list(set(e.url for e in self.network_errors))


class FrontendErrorCollectorFixture:
    """前端错误收集器的 pytest fixture 版本"""

    def __init__(self, page):
        self.collector = FrontendErrorCollector(page)

    def __enter__(self):
        self.collector.start_recording()
        return self.collector

    def __exit__(self, *args):
        self.collector.stop_recording()
        self.collector.generate_report()


# 全局实例
frontend_error_collector = FrontendErrorCollector()


# 使用示例
def create_frontend_error_report(test_name: str, page) -> str:
    """为测试创建前端错误报告"""
    collector = FrontendErrorCollector(page)
    collector.start_recording()

    # 执行测试操作...

    collector.stop_recording()

    report_file = Path("test-results/frontend_errors") / f"{test_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return collector.generate_report(str(report_file))