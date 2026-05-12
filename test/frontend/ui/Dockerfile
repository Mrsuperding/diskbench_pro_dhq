# UI Test Docker Container
# ========================
# 用于 CI/CD 环境的容器化测试

FROM python:3.14-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Node.js (用于前端构建)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制测试文件
COPY test/frontend/ui/ /app/test/

# 安装 Python 测试依赖
RUN pip install --no-cache-dir \
    pytest>=7.4.0 \
    pytest-playwright>=0.4.0 \
    playwright>=1.40.0 \
    pytest-xdist>=3.5.0 \
    pytest-rerunfailures>=13.0 \
    allure-pytest>=2.13.0 \
    pyyaml>=6.0 \
    python-dateutil>=2.8.0

# 安装 Playwright 浏览器
RUN playwright install --with-deps chromium

# 设置环境变量
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV TEST_ENV=dev

# 创建结果目录
RUN mkdir -p /app/test-results/screenshots \
    /app/test-results/videos \
    /app/test-results/html \
    /app/test-results/allure-results

# 默认命令
CMD ["pytest", "-v", "--alluredir=/app/test-results/allure-results"]