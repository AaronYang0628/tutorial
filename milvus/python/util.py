
import os
from glob import glob
import logging

logger = logging.getLogger('util')

def embedding_text(client, text, model):
    return (
        client.embeddings.create(input=text, model=model)
        .data[0]
        .embedding
    )

def read_markdown(path, recursive=True):
    logger.info(f"Current working directory: {os.getcwd()}")
    raw_text_lines = []
    for file_path in glob(path, recursive=recursive):
        with open(file_path, "r") as file:
            logger.info(f"processing file at {file_path}")
            file_text = file.read()
        raw_text_lines += file_text.split("# ")
    return raw_text_lines