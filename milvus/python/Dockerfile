# 使用 Python 3.12 官方镜像作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV HOST=0.0.0.0
ENV PORT=30500
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

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