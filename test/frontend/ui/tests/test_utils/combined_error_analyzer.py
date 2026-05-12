"""
Combined Error Analyzer - 前后端错误综合分析器
==============================================
收集、关联和分析前后端错误

用法：
    from test_utils.combined_error_analyzer import CombinedAnalyzer

    analyzer = CombinedAnalyzer()
    analyzer.start()

    # 执行测试...

    report = analyzer.generate_report()
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class ErrorPair:
    """错误对 - 关联的前后端错误"""
    frontend_error: Dict
    backend_error: Dict
    correlation_type: str  # "validation", "database", "auth", "unknown"
    description: str
    suggested_fix: str


@dataclass
class RootCauseAnalysis:
    """根本原因分析"""
    error_category: str
    symptom: str
    possible_causes: List[str]
    recommended_actions: List[str]
    related_errors: List[Dict]


class CombinedErrorAnalyzer:
    """前后端错误综合分析器"""

    def __init__(self):
        self.frontend_errors: List[Dict] = []
        self.backend_errors: List[Dict] = []
        self.api_requests: List[Dict] = []
        self.error_pairs: List[ErrorPair] = []
        self.root_cause_analysis: List[RootCauseAnalysis] = []
        self.log_dir = Path("test-results/combined_analysis")
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def clear(self):
        """清空所有数据"""
        self.frontend_errors.clear()
        self.backend_errors.clear()
        self.api_requests.clear()
        self.error_pairs.clear()
        self.root_cause_analysis.clear()

    def add_frontend_error(self, error: Dict):
        """添加前端错误"""
        self.frontend_errors.append({
            "timestamp": datetime.now().isoformat(),
            **error
        })

    def add_backend_error(self, error: Dict):
        """添加后端错误"""
        self.backend_errors.append(error)

    def add_api_request(self, request: Dict):
        """添加 API 请求"""
        self.api_requests.append(request)

    def correlate_errors(self) -> List[ErrorPair]:
        """关联前后端错误"""
        pairs = []

        # 遍历前端错误，找到对应的后端错误
        for fe in self.frontend_errors:
            # 尝试通过 request_id 关联
            if "request_id" in fe:
                for be in self.backend_errors:
                    if be.get("request_id") == fe["request_id"]:
                        pair = self._create_error_pair(fe, be)
                        if pair:
                            pairs.append(pair)
                        break

            # 尝试通过 URL 模式关联
            if "url" in fe:
                for be in self.backend_errors:
                    if self._urls_match(fe["url"], be.get("endpoint", "")):
                        pair = self._create_error_pair(fe, be)
                        if pair and pair not in pairs:
                            pairs.append(pair)

        self.error_pairs = pairs
        return pairs

    def _create_error_pair(self, frontend_error: Dict, backend_error: Dict) -> Optional[ErrorPair]:
        """创建错误对"""
        # 确定错误类型
        be_detail = backend_error.get("detail", {})
        correlation_type = "unknown"
        description = ""
        suggested_fix = ""

        if isinstance(be_detail, dict):
            error_msg = str(be_detail.get("message", ""))
        elif isinstance(be_detail, str):
            error_msg = be_detail
        else:
            error_msg = str(be_detail)

        # 根据错误类型确定关联类型和建议修复
        if "validation" in error_msg.lower() or "missing" in error_msg.lower() or "required" in error_msg.lower():
            correlation_type = "validation"
            description = "前端未提供必填字段或字段格式不正确"
            suggested_fix = "检查表单验证逻辑，确保必填字段已填写且格式正确"
        elif "not found" in error_msg.lower() or "不存在" in error_msg:
            correlation_type = "not_found"
            description = "请求的资源不存在"
            suggested_fix = "检查前端传递的资源 ID 是否正确"
        elif "foreign key" in error_msg.lower() or "partition" in error_msg.lower():
            correlation_type = "database"
            description = "数据库外键约束或分区关联错误"
            suggested_fix = "检查分区是否正确创建，或资源是否已删除"
        elif "auth" in error_msg.lower() or "permission" in error_msg.lower() or "无权" in error_msg:
            correlation_type = "auth"
            description = "权限验证失败"
            suggested_fix = "检查用户是否有所需权限，或 token 是否过期"
        elif "already exists" in error_msg.lower() or "已存在" in error_msg:
            correlation_type = "duplicate"
            description = "尝试创建重复资源"
            suggested_fix = "检查是否已有同名资源，或使用唯一标识符"
        else:
            description = "未知错误类型"
            suggested_fix = "查看详细错误信息并手动排查"

        return ErrorPair(
            frontend_error=frontend_error,
            backend_error=backend_error,
            correlation_type=correlation_type,
            description=description,
            suggested_fix=suggested_fix
        )

    def _urls_match(self, url1: str, url2: str) -> bool:
        """检查 URL 是否匹配（去除参数和路径变量）"""
        # 简化匹配：只比较路径部分
        path1 = url1.split("?")[0].split("/")[-2:]
        path2 = url2.split("?")[0].split("/")[-2:]
        return path1 == path2

    def analyze_root_causes(self) -> List[RootCauseAnalysis]:
        """分析根本原因"""
        analyses = []

        # 按错误类型分组
        errors_by_type = defaultdict(list)
        for pair in self.error_pairs:
            errors_by_type[pair.correlation_type].append(pair)

        # 为每种错误类型生成分析
        for error_type, pairs in errors_by_type.items():
            if error_type == "validation":
                analysis = RootCauseAnalysis(
                    error_category="参数验证错误",
                    symptom="前端提交的数据在后端验证失败",
                    possible_causes=[
                        "前端表单验证规则与后端不一致",
                        "必填字段在前端被隐藏或禁用",
                        "数据类型转换错误（如字符串 vs 数字）",
                        "字段名称拼写错误（camelCase vs snake_case）"
                    ],
                    recommended_actions=[
                        "统一前后端的字段命名和验证规则",
                        "检查 CaseFormDialog 和 TaskFormDialog 中的字段映射",
                        "确保所有必填字段在前端可见且可编辑"
                    ],
                    related_errors=[p.backend_error for p in pairs]
                )
                analyses.append(analysis)

            elif error_type == "database":
                analysis = RootCauseAnalysis(
                    error_category="数据库错误",
                    symptom="数据操作失败或数据一致性错误",
                    possible_causes=[
                        "分区记录不存在",
                        "外键约束冲突",
                        "数据库连接超时"
                    ],
                    recommended_actions=[
                        "检查 NodePartition 表中是否有对应记录",
                        "确保节点创建时自动创建默认分区",
                        "增加数据库连接池重试机制"
                    ],
                    related_errors=[p.backend_error for p in pairs]
                )
                analyses.append(analysis)

            elif error_type == "auth":
                analysis = RootCauseAnalysis(
                    error_category="权限/认证错误",
                    symptom="用户无权限执行操作",
                    possible_causes=[
                        "用户角色不匹配",
                        "Token 过期",
                        "资源所有权验证失败"
                    ],
                    recommended_actions=[
                        "检查用户的 role 字段",
                        "实现 token 自动刷新机制",
                        "验证资源创建者和当前用户的关系"
                    ],
                    related_errors=[p.backend_error for p in pairs]
                )
                analyses.append(analysis)

            elif error_type == "not_found":
                analysis = RootCauseAnalysis(
                    error_category="资源不存在",
                    symptom="请求的资源在数据库中找不到",
                    possible_causes=[
                        "资源已被删除",
                        "ID 传递错误",
                        "级联删除导致关联资源不存在"
                    ],
                    recommended_actions=[
                        "检查前端传递的 ID 是否有效",
                        "实现资源的软删除机制",
                        "在删除前检查关联资源"
                    ],
                    related_errors=[p.backend_error for p in pairs]
                )
                analyses.append(analysis)

        self.root_cause_analysis = analyses
        return analyses

    def generate_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """生成综合报告"""
        # 先进行关联和分析
        self.correlate_errors()
        self.analyze_root_causes()

        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.log_dir / f"combined_analysis_{timestamp}.json"

        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_frontend_errors": len(self.frontend_errors),
                "total_backend_errors": len(self.backend_errors),
                "total_api_requests": len(self.api_requests),
                "error_pairs_found": len(self.error_pairs),
                "root_cause_analyses": len(self.root_cause_analysis)
            },
            "frontend_errors": self.frontend_errors,
            "backend_errors": self.backend_errors,
            "api_requests": self.api_requests,
            "error_pairs": [
                {
                    "frontend_error": ep.front-end_error,
                    "backend_error": ep.backend_error,
                    "correlation_type": ep.correlation_type,
                    "description": ep.description,
                    "suggested_fix": ep.suggested_fix
                }
                for ep in self.error_pairs
            ],
            "root_cause_analysis": [
                {
                    "error_category": rca.error_category,
                    "symptom": rca.symptom,
                    "possible_causes": rca.possible_causes,
                    "recommended_actions": rca.recommended_actions,
                    "related_errors_count": len(rca.related_errors)
                }
                for rca in self.root_cause_analysis
            ]
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return report

    def generate_markdown_report(self, output_file: Optional[str] = None) -> str:
        """生成 Markdown 格式的综合报告"""
        self.generate_report()

        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.log_dir / f"combined_analysis_{timestamp}.md"

        md = []
        md.append("# Combined Error Analysis Report")
        md.append(f"\n**Generated:** {datetime.now().isoformat()}\n")

        md.append("## Summary")
        md.append(f"- Frontend Errors: {len(self.frontend_errors)}")
        md.append(f"- Backend Errors: {len(self.backend_errors)}")
        md.append(f"- API Requests: {len(self.api_requests)}")
        md.append(f"- Correlated Error Pairs: {len(self.error_pairs)}")
        md.append(f"- Root Cause Analyses: {len(self.root_cause_analysis)}")

        if self.error_pairs:
            md.append("\n## Error Correlation Results")
            for i, pair in enumerate(self.error_pairs, 1):
                md.append(f"\n### {i}. {pair.correlation_type.upper()} Error")
                md.append(f"**Description:** {pair.description}")
                md.append(f"**Suggested Fix:** {pair.suggested_fix}")
                md.append(f"\n**Frontend Error:**")
                md.append(f"  - URL: {pair.front-end_error.get('url', 'N/A')}")
                md.append(f"  - Message: {pair.front-end_error.get('text', 'N/A')}")
                md.append(f"\n**Backend Error:**")
                md.append(f"  - Endpoint: {pair.backend_error.get('endpoint', 'N/A')}")
                md.append(f"  - Message: {pair.backend_error.get('message', 'N/A')}")
                md.append(f"  - Request ID: {pair.backend_error.get('request_id', 'N/A')}")

        if self.root_cause_analysis:
            md.append("\n## Root Cause Analysis")
            for i, rca in enumerate(self.root_cause_analysis, 1):
                md.append(f"\n### {i}. {rca.error_category}")
                md.append(f"**Symptom:** {rca.symptom}")
                md.append(f"\n**Possible Causes:**")
                for cause in rca.possible_causes:
                    md.append(f"- {cause}")
                md.append(f"\n**Recommended Actions:**")
                for action in rca.recommended_actions:
                    md.append(f"- {action}")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(md))

        return str(output_file)

    def print_summary(self):
        """打印摘要到控制台"""
        print("\n" + "=" * 60)
        print("COMBINED ERROR ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Frontend Errors: {len(self.frontend_errors)}")
        print(f"Backend Errors: {len(self.backend_errors)}")
        print(f"API Requests: {len(self.api_requests)}")
        print(f"Correlated Error Pairs: {len(self.error_pairs)}")
        print(f"Root Cause Analyses: {len(self.root_cause_analysis)}")

        if self.error_pairs:
            print("\n--- Error Correlations ---")
            for i, pair in enumerate(self.error_pairs, 1):
                print(f"{i}. [{pair.correlation_type}] {pair.description}")

        if self.root_cause_analysis:
            print("\n--- Root Causes ---")
            for i, rca in enumerate(self.root_cause_analysis, 1):
                print(f"{i}. {rca.error_category}: {rca.symptom}")

        print("=" * 60 + "\n")


class TestErrorCollector:
    """测试错误收集器（pytest 集成）"""

    def __init__(self):
        self.analyzer = CombinedErrorAnalyzer()
        self.test_name = ""
        self.start_time = None

    def start_test(self, test_name: str):
        """开始收集测试错误"""
        self.test_name = test_name
        self.start_time = datetime.now()
        self.analyzer.clear()

    def add_error(self, source: str, error: Dict):
        """添加错误"""
        if source == "frontend":
            self.analyzer.add_frontend_error(error)
        elif source == "backend":
            self.analyzer.add_backend_error(error)
        elif source == "api":
            self.analyzer.add_api_request(error)

    def end_test(self) -> Dict:
        """结束测试并生成报告"""
        report = self.analyzer.generate_report()
        return report


# 全局实例
combined_analyzer = CombinedErrorAnalyzer()


# 快速分析函数
def quick_analysis(frontend_errors: List[Dict], backend_errors: List[Dict]) -> Dict[str, Any]:
    """快速分析错误"""
    analyzer = CombinedErrorAnalyzer()
    analyzer.frontend_errors = frontend_errors
    analyzer.backend_errors = backend_errors
    analyzer.correlate_errors()
    analyzer.analyze_root_causes()
    return {
        "summary": {
            "total_frontend_errors": len(frontend_errors),
            "total_backend_errors": len(backend_errors),
            "error_pairs_found": len(analyzer.error_pairs)
        },
        "error_pairs": analyzer.error_pairs,
        "root_causes": analyzer.root_cause_analysis
    }