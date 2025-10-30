import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger_util import setup_logging

# 在模块加载时设置默认日志器
logger = setup_logging('embedding.util')

def embed_text(client, text, model):
    return (
        client.embeddings.create(input=text, model=model)
        .data[0]
        .embedding
    )

