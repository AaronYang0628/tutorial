
import configparser

from PIL import Image
import os
from pymilvus import MilvusClient
from feature_extractor import FeatureExtractor

cfp = configparser.RawConfigParser()
# 使用脚本文件所在目录的路径
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config.ini')
cfp.read(config_path)
milvus_uri = cfp.get('example', 'uri')
token = cfp.get('example', 'token')
collection_name = cfp.get('example', 'collection')

extractor = FeatureExtractor("resnet34")

milvus_client = MilvusClient(uri=milvus_uri, token=token)

# Create a collection in quick setup mode
if milvus_client.has_collection(collection_name=collection_name):
    milvus_client.drop_collection(collection_name=collection_name)
milvus_client.create_collection(
    collection_name=collection_name,
    vector_field_name="vector",
    dimension=512,
    auto_id=True,
    enable_dynamic_field=True,
    metric_type="COSINE",
)


root = "E:/Github_Self/tutorial/milvus/python/reverse_image_search"
insert = True
if insert is True:
    for _, foldername, filenames in os.walk(root + "/train"):
        for filename in filenames:
            if filename.endswith(".JPEG"):
                milvus_client.insert(collection_name,
                    {"vector": extractor(filepath), "filename": filepath},
                )
