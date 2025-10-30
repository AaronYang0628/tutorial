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