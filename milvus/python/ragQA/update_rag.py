import time

from tqdm import tqdm
from pymilvus import MilvusClient
from openai import OpenAI
from milvus.python.util import embedding_text, read_markdown


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

if os.environ.get("MODE", "create") == "create":
    cooked_data = []

    raw_text_lines = read_markdown(os.environ.get("EXT_DOC_PATH", "milvus_docs/en/faq/*.md"))
    
    if milvus_client.has_collection(collection_name):
        milvus_client.drop_collection(collection_name)
        print(f"Dropped the existing collection {collection_name} successfully")
    
    milvus_client.create_collection(
        collection_name=collection_name,
        dimension=embedding_dim,
        metric_type="IP", 
        consistency_level="Bounded",
    )

    collection_property = milvus_client.describe_collection(collection_name)
    print("Collection details: %s" % collection_property)

    for i, line in enumerate(tqdm(raw_text_lines, desc="Creating embeddings")):
        cooked_data.append({"id": i, "vector": embedding_text(openai_client, line, os.environ.get("EMBEDDING_MODEL", "")), "text": line})

    milvus_client.insert(collection_name=collection_name, data=cooked_data)

elif os.environ.get("MODE", "append") == "append":
    if milvus_client.has_collection(collection_name):
        cooked_data = []

        raw_text_lines = read_markdown(os.environ.get("EXT_DOC_PATH", "milvus_docs/en/faq/*.md"))
        
        for i, line in enumerate(tqdm(raw_text_lines, desc="Creating embeddings")):
            cooked_data.append({"id": i, "vector": embedding_text(openai_client, line, os.environ.get("EMBEDDING_MODEL", "")), "text": line})

        milvus_client.insert(collection_name=collection_name, data=cooked_data)
        
else:
    print(f"Unknown mode {os.environ.get("MODE")}")


print("Start to flush")
start_flush = time.time()
milvus_client.flush(collection_name)
end_flush = time.time()
print(f"Flush completed in {round(end_flush - start_flush, 4)} seconds")

