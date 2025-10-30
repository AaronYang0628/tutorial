### Running
1. init flask env
```shell
pip install --upgrade pymilvus openai requests tqdm python-dotenv flask flask_cors flask-restx
```

### Development
1. build venv
```shell
python3 -m venv .venv
source venv/bin/activate
```
1. rag
```shell
pip install --upgrade pymilvus 
```

2. image search
```shell
pip install --upgrade pymilvus scikit-learn timm
```

3. build image
```shell
docker build -t milvus-rag-app:v20251030r1 .
```


kubectl -n application  create secret generic milvus-rag-secrets \
  --from-literal=milvus_uri='https://in03-891eca6c21bd4e5.serverless.aws-eu-central-1.cloud.zilliz.com' \
  --from-literal=milvus_token='32dc6e16e03c11d52247a455ed827bb856077f1603b6b60b4d71f60b7a5f238b9ce73960ce9d4bda9aa9378a800bb9d8d521ec42' \
  --from-literal=tongyi_api_key='sk-f0029ee74a454bddbe1a79c2d55aaca3'