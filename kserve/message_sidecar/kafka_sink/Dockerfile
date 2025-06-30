FROM m.daocloud.io/docker.io/library/python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir  -r requirements.txt 

COPY model.py .

CMD ["python", "model.py", "--model_name=kafka-sink"]