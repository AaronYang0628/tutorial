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

from setuptools import setup, find_packages

tests_require = ["pytest", "mypy"]

setup(
    name="transformer",
    version="0.2.0",
    author_email="dsun20@bloomberg.net",
    license="../../LICENSE.txt",
    url="https://github.com/kserve/kserve/tree/master/docs/samples/kafka",
    description="Transformer",
    long_description=open("README.md").read(),
    python_requires=">=3.11",
    packages=find_packages("transformer"),
    install_requires=[
        "kserve>0.10.0",
        "kafka-python>=2.0.2",
        "cloudevents>=1.0.0",
        "pillow>=10.3.0"
    ],
    tests_require=tests_require,
    extras_require={"test": tests_require},
)
