FROM python:3.9-slim

ARG KAFKA_TOPIC="mnist-topic"
ARG KAFKA_BOOTSTRAP_SERVERS="localhost:9092"

ENV KAFKA_TOPIC=${KAFKA_TOPIC}
ENV KAFKA_BOOTSTRAP_SERVERS=${KAFKA_BOOTSTRAP_SERVERS}

RUN apt-get update && apt-get install -y libglib2.0-0
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir kserve
COPY . .
RUN pip install --no-cache-dir -e .
ENTRYPOINT ["python", "-m", "kafka_sink"]
