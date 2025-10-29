# 使用 Python 3.12 官方镜像作为构建阶段
FROM python:3.12-slim as builder

# 设置工作目录
WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 第二阶段：最终镜像
FROM python:3.12-slim

WORKDIR /app

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 设置环境变量
ENV HOST=0.0.0.0
ENV PORT=30500
ENV PYTHONUNBUFFERED=1

# 复制应用代码和静态文件
COPY app.py .
COPY index.html .
COPY util.py .
COPY imgSearch/feature_extractor.py ./imgSearch/feature_extractor.py

# 创建上传文件夹
RUN mkdir -p uploads

# 暴露端口
EXPOSE 30500

# 运行应用
CMD ["python", "app.py"]