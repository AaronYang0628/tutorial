#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from typing import Dict, Union

import cloudevents
from cloudevents.conversion import to_structured
from cloudevents.http import CloudEvent

import kserve
from kserve import InferRequest, InferResponse
from kserve.protocol.grpc.grpc_predict_v2_pb2 import ModelInferResponse
from kserve.logging import logger

request_key = "request_key"

class KafkaSink(kserve.Model):
    def __init__(self, name: str, predictor_host: str):
        super().__init__(name)
        self.predictor_host = predictor_host
        self._key = None
        self._kafka_bootstrap_servers = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self._kafka_topic = os.environ.get('KAFKA_TOPIC', 'mnist-topic')
        slef._producer = KafkaProducer(bootstrap_servers=self._kafka_bootstrap_servers)

    async def preprocess(
        self, inputs: Union[Dict, InferRequest], headers: Dict[str, str] = None
    ) -> Union[Dict, InferRequest]:
        logger.info("Received inputs %s", inputs)
        # might need to modify the inputs, add a request key
        inputs[request_key] = random.randint(0, 1000000) + ""
        return inputs;

    async def postprocess(
        self,
        response: Union[Dict, InferResponse, ModelInferResponse],
        headers: Dict[str, str] = None,
    ) -> Union[Dict, ModelInferResponse]:
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
        self._producer.send(self._kafka_topic, value=result)
        return response
