"""
Configuration Loader - 多环境配置加载器
========================================
支持从 YAML 文件加载不同环境的配置

用法：
    from config.settings import ConfigLoader

    config = ConfigLoader("dev")  # 加载 dev 环境配置
    base_url = config.base_url     # http://localhost:3000
    admin_creds = config.get("users", "admin")

命令行参数：
    pytest --env test  # 加载 test 环境配置

环境变量：
    TEST_ENV - 可通过环境变量设置，默认 "dev"
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    多环境配置加载器

    配置目录结构：
        config/
            environments/
                dev.yaml
                test.yaml
                staging.yaml
                prod.yaml
            settings.py
    """

    DEFAULT_ENV = "dev"
    CONFIG_DIR = Path(__file__).parent
    ENV_DIR = CONFIG_DIR / "environments"

    # 默认配置（所有环境共享）
    DEFAULTS = {
        "app": {
            "base_url": "http://localhost:3000",
            "api_url": "http://localhost:8000",
            "timeout": 30000,
            "viewport": {"width": 1920, "height": 1080},
        },
        "wait": {
            "element": 30000,
            "navigation": 30000,
            "response": 10000,
        },
        "retry": {
            "max_attempts": 2,
            "delay": 1,
        },
        "screenshot": {
            "on_failure": True,
            "full_page": True,
            "directory": "test-results/screenshots",
        },
        "video": {
            "on_failure": False,
            "directory": "test-results/videos",
        },
    }

    def __init__(self, env: Optional[str] = None):
        """
        初始化配置加载器

        Args:
            env: 环境名称 (dev/test/staging/prod)，默认从 --env 参数或 TEST_ENV 环境变量读取
        """
        self.env = env or os.environ.get("TEST_ENV") or self.DEFAULT_ENV
        self._config = self._load_config()
        logger.info(f"Configuration loaded for environment: {self.env}")

    def _load_config(self) -> Dict:
        """加载配置文件"""
        config_file = self.ENV_DIR / f"{self.env}.yaml"

        # 合并默认配置
        merged = self.DEFAULTS.copy()

        if config_file.exists():
            with open(config_file, encoding="utf-8") as f:
                env_config = yaml.safe_load(f) or {}
                merged = self._deep_merge(merged, env_config)
        else:
            logger.warning(f"Config file not found: {config_file}, using defaults")

        return merged

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """深度合并字典"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def get(self, *keys, default: Any = None) -> Any:
        """
        获取嵌套配置值

        Args:
            keys: 嵌套键路径，如 get("app", "base_url")
            default: 默认值

        Returns:
            配置值或默认值
        """
        value = self._config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        return value if value is not None else default

    def get_section(self, section: str) -> Dict:
        """获取配置节"""
        return self.get(section) or {}

    # ========== 快捷属性 ==========

    @property
    def base_url(self) -> str:
        """应用基础 URL"""
        return self.get("app", "base_url", default="http://localhost:3000")

    @property
    def api_url(self) -> str:
        """API URL"""
        return self.get("app", "api_url", default="http://localhost:8000")

    @property
    def timeout(self) -> int:
        """默认超时时间（毫秒）"""
        return self.get("app", "timeout", default=30000)

    @property
    def viewport(self) -> Dict[str, int]:
        """浏览器视口大小"""
        return self.get("app", "viewport", default={"width": 1920, "height": 1080})

    # ========== 用户配置 ==========

    @property
    def users(self) -> Dict[str, Dict[str, str]]:
        """获取所有用户配置"""
        return self.get("users") or {}

    def get_user(self, username: str) -> Optional[Dict[str, str]]:
        """获取指定用户配置"""
        return self.users.get(username)

    @property
    def admin_user(self) -> Dict[str, str]:
        """获取管理员用户配置"""
        # 尝试多种可能的 admin 用户名
        for admin_name in ["admin", "administrator", "root"]:
            user = self.get_user(admin_name)
            if user:
                return user
        # 回退到硬编码默认值
        return {"username": "admin", "password": "admin123", "role": "admin"}

    @property
    def demo_user(self) -> Dict[str, str]:
        """获取演示用户配置"""
        user = self.get_user("demo")
        if user:
            return user
        return {"username": "demo", "password": "demo123", "role": "user"}

    # ========== 等待配置 ==========

    @property
    def element_timeout(self) -> int:
        """元素等待超时（毫秒）"""
        return self.get("wait", "element", default=30000)

    @property
    def navigation_timeout(self) -> int:
        """导航等待超时（毫秒）"""
        return self.get("wait", "navigation", default=30000)

    @property
    def response_timeout(self) -> int:
        """响应等待超时（毫秒）"""
        return self.get("wait", "response", default=10000)

    # ========== 重试配置 ==========

    @property
    def max_retry_attempts(self) -> int:
        """最大重试次数"""
        return self.get("retry", "max_attempts", default=2)

    @property
    def retry_delay(self) -> int:
        """重试延迟（秒）"""
        return self.get("retry", "delay", default=1)

    # ========== 截图/录像配置 ==========

    @property
    def screenshot_on_failure(self) -> bool:
        """失败时自动截图"""
        return self.get("screenshot", "on_failure", default=True)

    @property
    def screenshot_full_page(self) -> bool:
        """截图时截取完整页面"""
        return self.get("screenshot", "full_page", default=True)

    @property
    def screenshot_directory(self) -> str:
        """截图保存目录"""
        return self.get("screenshot", "directory", default="test-results/screenshots")

    @property
    def video_on_failure(self) -> bool:
        """失败时自动录制"""
        return self.get("video", "on_failure", default=False)

    @property
    def video_directory(self) -> str:
        """录像保存目录"""
        return self.get("video", "directory", default="test-results/videos")

    # ========== 基础设施错误列表 ==========

    @property
    def known_infra_errors(self) -> list:
        """已知的非应用错误关键字（不会导致测试失败）"""
        return self.get("infra_errors", "keywords") or [
            "Socket.IO",
            "xhr poll error",
            "TransportError",
            "socket.io-client",
            "favicon.ico",
            "Failed to load resource: the server responded with a status of 404",
            "Failed to load resource: the server responded with a status of 401",
            "Failed to load resource: the server responded with a status of 500",
            "Failed to load resource: the server responded with a status of 503",
        ]

    def __repr__(self) -> str:
        return f"ConfigLoader(env='{self.env}')"