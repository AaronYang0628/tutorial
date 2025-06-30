FROM m.daocloud.io/docker.io/python:3.9-slim-bullseye

# Upgrade system packages to reduce vulnerabilities
RUN apt-get update && apt-get upgrade -y && apt-get install -y libglib2.0-0

ARG KAFKA_TOPIC="mnist-topic"
ARG KAFKA_BOOTSTRAP_SERVERS="localhost:9092"

# (Moved to the previous RUN command for efficiency)
ENV KAFKA_BOOTSTRAP_SERVERS=${KAFKA_BOOTSTRAP_SERVERS}

RUN apt-get update && apt-get install -y libglib2.0-0
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir kserve
COPY . .
RUN pip install --no-cache-dir -e .
ENTRYPOINT ["python", "-m", "kafka_sink"]
