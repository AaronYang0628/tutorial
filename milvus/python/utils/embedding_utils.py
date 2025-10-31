import os
import sys
import httpx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger_util import setup_logging
from utils.env_utils import load_env_config


logger = setup_logging('embedding.util')

load_env_config("../.env")

def embed_text(openai_client, text, model):
    if os.environ.get("EMBEDDING_MODEL").startswith("customize"):
        logger.info(f"going to use embedding model: {os.environ.get('EMBEDDING_MODEL')} with base url: {os.environ.get('EMBEDDING_BASE_URL')}")
        http_client = httpx.Client(base_url=os.environ.get("EMBEDDING_BASE_URL"))
        return (
            http_client.post("/embed", json={
                "texts": [text],
                "batch_size": 64
            })
            .json()["embeddings"][0]
        )
    else:
        logger.info(f"going to use embedding openai model: {model} with base url: {os.environ.get('EMBEDDING_BASE_URL')}")
        return (
            openai_client.embeddings.create(input=text, model=model)
            .data[0]
            .embedding
    )
