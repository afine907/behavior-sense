# BehaviorSense Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml .

# 安装 Python 依赖
RUN pip install --no-cache-dir pip --upgrade && \
    pip install --no-cache-dir .

# 复制代码
COPY . .

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# 默认环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO

# 默认命令 (可被覆盖)
CMD ["uvicorn", "behavior_insight.main:app", "--host", "0.0.0.0", "--port", "8000"]
