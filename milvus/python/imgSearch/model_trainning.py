
import os
import sys
from pymilvus import MilvusClient
from feature_extractor import FeatureExtractor

# 添加系统路径以便导入utils模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.env_utils import load_env_config
from utils.logger_util import setup_logging

# 设置日志器
logger = setup_logging('imgSearch.model_training')

# 加载环境变量配置
load_env_config("../.env")

# 从环境变量读取配置
milvus_uri = os.environ.get("MILVUS_URI", "http://localhost:19530")
token = os.environ.get("MILVUS_TOKEN", "")
collection_name = os.environ.get("IMAGE_COLLECTION_NAME", "image_embeddings")

extractor = FeatureExtractor("resnet34")

# 初始化Milvus客户端
milvus_client = MilvusClient(uri=milvus_uri, token=token)
logger.info(f"Connected to Milvus: {milvus_uri} successfully")

# Create a collection in quick setup mode
if milvus_client.has_collection(collection_name=collection_name):
    milvus_client.drop_collection(collection_name=collection_name)
    logger.info(f"Dropped existing collection: {collection_name}")

milvus_client.create_collection(
    collection_name=collection_name,
    vector_field_name="vector",
    dimension=512,
    auto_id=True,
    enable_dynamic_field=True,
    metric_type="COSINE",
)
logger.info(f"Created collection: {collection_name} with dimension 512")


root = os.environ.get("TRAIN_IMAGE_ROOT_PATH", "E:/Github_Self/tutorial/milvus/python/uploads/preset/images")


logger.info(f"Starting image feature extraction and insertion from: {root}/train")
inserted_count = 0
for _, __, filenames in os.walk(root + "/train"):
    for filename in filenames:
        if filename.endswith(".JPEG"):
            abs_file_path = os.path.join(_, filename)
            logger.info(f"Processing file: {abs_file_path}")
            rel_file_path = os.path.relpath(abs_file_path, root)

            try:
                # 提取特征并插入
                milvus_client.insert(
                    collection_name,
                    {"vector": extractor(abs_file_path), "filepath": rel_file_path},
                )
                inserted_count += 1
                if inserted_count % 100 == 0:
                    logger.info(f"Inserted {inserted_count} images so far")
            except Exception as e:
                logger.error(f"Error processing file {abs_file_path}: {str(e)}")

logger.info(f"Image training completed. Total images inserted: {inserted_count}")

