import argparse
import os
from typing import Dict, Union

from typing import Dict


import kserve
from kserve import InferRequest,InferResponse 
from kserve.utils.utils import generate_uuid
from kserve.logging import logger

from kafka import KafkaProducer
import json
from cloudevents.conversion import to_structured
from cloudevents.http import CloudEvent



request_key = "request_key"

kafka_producer = KafkaProducer(
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    bootstrap_servers=os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
)

class KafkaSink(kserve.Model):
    def __init__(self, name: str):
        super().__init__(name)
        self.predictor_host = predictor_host
        self._key = None
        self._kafka_topic = os.environ.get('KAFKA_TOPIC', 'test-topic')

    async def preprocess(
        self, inputs: Union[Dict, InferRequest], headers: Dict[str, str] = None
    ) -> Union[Dict, InferRequest]:
        logger.info("Received inputs %s", inputs)
        # might need to modify the inputs, add a request key
        inputs[request_key] = generate_uuid()
        return inputs;

    async def postprocess(
        self,
        response: Union[Dict, InferResponse],
        headers: Dict[str, str] = None,
    ) -> Union[Dict, InferResponse]:
        logger.info("postprocess headers: %s", headers)
        logger.info("postprocess response: %s", response)
        index = response["predictions"][0]["classes"]
        logger.info("digit:" + str(index))

        attributes = {
            "type": "com.example.sampletype2",
            "source": "https://example.com/event-producer",
        }
        data = {"message": "Hello World!"}
        cloudevent = CloudEvent(attributes, data)
        _, result = to_structured(cloudevent)
        kafka_producer.send(self._kafka_topic, value=result)
        return response


