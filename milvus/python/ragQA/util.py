
import os
from glob import glob
import logging

logger = logging.getLogger('qa.rag.util')

def embedding_text(client, text, model):
    return (
        client.embeddings.create(input=text, model=model)
        .data[0]
        .embedding
    )
