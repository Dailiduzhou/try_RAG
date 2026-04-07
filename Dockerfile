FROM python:3.13-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 安装uv
RUN pip install --no-cache-dir uv

# 复制依赖定义文件
COPY pyproject.toml uv.lock ./

# 使用uv安装依赖（利用Docker缓存）
RUN uv sync --frozen --no-dev

# 复制应用代码
COPY main.py ./
COPY config.yaml.example ./config.yaml.example

# 创建data目录
RUN mkdir -p data

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 默认命令
CMD ["uv", "run", "main.py"]
