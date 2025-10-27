
import os
from glob import glob

def embedding_text(client, text, model):
    return (
        client.embeddings.create(input=text, model=model)
        .data[0]
        .embedding
    )

def read_markdown(path, recursive: True):
    raw_text_lines = []
    for file_path in glob(path, recursive=recursive):
        with open(file_path, "r") as file:
            file_text = file.read()
        raw_text_lines += file_text.split("# ")
    return raw_text_lines