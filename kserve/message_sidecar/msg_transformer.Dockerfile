FROM m.daocloud.io/docker.io/library/python:3.11-slim

RUN apt-get update && apt-get install -y libglib2.0-0
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir kserve kafka-python cloudevents pillow>=10.3.0,<11.0.0
COPY . .
RUN pip install --no-cache-dir -e .

ENTRYPOINT ["python", "-m", "msg_transformer"]