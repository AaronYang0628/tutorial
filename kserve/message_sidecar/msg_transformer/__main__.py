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

import kserve
import argparse

from kserve import logging
from .kafka_sink import KafkaSink

DEFAULT_MODEL_NAME = "msg_transformer"

parser = argparse.ArgumentParser(parents=[kserve.model_server.parser])


args, _ = parser.parse_known_args()

if __name__ == "__main__":
    if args.configure_logging:
        logging.configure_logging(args.log_config_file)
    transformer = KafkaSink(DEFAULT_MODEL_NAME, predictor_host=args.predictor_host)
    server = kserve.ModelServer()
    server.start(models=[transformer])
