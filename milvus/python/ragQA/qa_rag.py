from dotenv import load_dotenv

load_dotenv()

import json
import os
from pymilvus import MilvusClient
from openai import OpenAI
from milvus.python.util import embedding_text


milvus_uri = os.environ.get("MILVUS_URI", "http://localhost:19530")
token = os.environ.get("MILVUS_TOKEN", "")
collection_name = os.environ.get("MILVUS_COLLECTION", "default_collection")
embedding_dim = int(os.environ.get("EMBEDDING_DIM", "1024"))

openai_client = OpenAI(
        api_key=os.environ.get("TONGYI_API_KEY", os.environ.get("OPENAI_API_KEY", "")),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

milvus_client = MilvusClient(uri=milvus_uri, token=token)

print(f"Connected to DB: {milvus_uri} successfully")

if milvus_client.has_collection(collection_name):
    question = "How is data stored in milvus?"
    search_res = milvus_client.search(
        collection_name=collection_name,
        data=[
            embedding_text(openai_client, question, os.environ.get("EMBEDDING_MODEL", ""))
        ],  
        limit=int(os.environ.get("GRABE_TOP_N_RES", "5")), 
        search_params={"metric_type": "IP", "params": {}}, 
        output_fields=["text"], 
    )

    retrieved_lines_with_distances = [
        (res["entity"]["text"], res["distance"]) for res in search_res[0]
    ]
    print(json.dumps(retrieved_lines_with_distances, indent=4))

    context = "\n".join(
        [line_with_distance[0] for line_with_distance in retrieved_lines_with_distances]
    )

    SYSTEM_PROMPT = """
    Human: You are an AI assistant. You are able to find answers to the questions from the contextual passage snippets provided.
    """
    USER_PROMPT = f"""
    Use the following pieces of information enclosed in <context> tags to provide an answer to the question enclosed in <question> tags.
    <context>
    {context}
    </context>
    <question>
    {question}
    </question>
    """

    response = openai_client.chat.completions.create(
        model=os.environ.get("LLM_MODEL", "gpt-3.5-turbo"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ],
    )
    print(response.choices[0].message.content)
else:
    print(f"Cannot find collection {collection_name} in milvus: {milvus_uri}")