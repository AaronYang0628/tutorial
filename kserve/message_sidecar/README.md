### Message SideCar


### Kafka Sink
- build
```shell
podman build -t docker.io/aaron666/kserve-msg-sink:dev -f ./Dockerfile .
```
- test



### Kafka Transformer
```shell
podman build -t docker.io/aaron666/kserve-msg-sink:latest -f ./msg_transformer.Dockerfile .
```