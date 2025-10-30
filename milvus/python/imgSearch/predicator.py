import os
import sys

from pymilvus import MilvusClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from imgSearch.feature_extractor import FeatureExtractor
from utils.env_utils import load_env_config
from utils.logger_util import setup_logging

# 设置日志器
logger = setup_logging('imgSearch.predicator')


def get_similar_image_paths(query_image_path, milvus_client, extractor, collection_name, top_k=10):
    """
    获取相似图片的路径列表
    
    Args:
        query_image_path: 查询图像路径
        milvus_client: Milvus客户端实例
        extractor: 特征提取器实例
        collection_name: 集合名称
        top_k: 返回的相似图像数量
    
    Returns:
        list: 包含相似图像路径和相似度的字典列表
    """
    logger = setup_logging('imgSearch.predicator')
    logger.info(f"Searching similar images for: {query_image_path}")
    
    try:
        # 检查集合是否存在
        if not milvus_client.has_collection(collection_name):
            logger.error(f"Collection {collection_name} does not exist")
            return []
        
        # 提取查询图像特征并搜索
        query_features = extractor(query_image_path)
        results = milvus_client.search(
            collection_name,
            data=[query_features],
            limit=top_k,
            output_fields=["filepath", "filename"],  # 支持两种可能的字段名
            search_params={"metric_type": "COSINE"},
        )
        
        logger.info(f"Found {len(results[0])} similar images")
        
        # 处理结果
        similar_image_paths = []
        for hit in results[0]:
            # 尝试获取filepath字段，如果不存在则使用filename字段
            file_path = hit["entity"].get("filepath", hit["entity"].get("filename"))
            distance = hit["distance"]
            similarity = 1 - distance  
            
            logger.info(f"Similar image found: {file_path} (distance: {distance:.4f}, similarity: {similarity:.4f})")
            
            similar_image_paths.append({
                "path": file_path,
                "abs_path": os.path.join(os.environ.get('TRAIN_IMAGE_ROOT_PATH'), file_path),
                "distance": distance,
                "similarity": similarity
            })
        
        return similar_image_paths
        
    except Exception as e:
        logger.error(f"Error during image path search: {str(e)}")
        return []


if __name__ == "__main__":
    # 加载环境变量
    load_env_config("../.env")
    

    milvus_uri = os.environ.get('MILVUS_URI', 'http://localhost:19530')
    token = os.environ.get('MILVUS_TOKEN', '')
    collection_name = os.environ.get('IMAGE_COLLECTION_NAME', 'image_embeddings')
    
    logger.info(f"Connected to DB: {milvus_uri} successfully")
    milvus_client = MilvusClient(uri=milvus_uri, token=token)

    extractor = FeatureExtractor("resnet34")
    
    test_image_path = "E:/Github_Self/tutorial/milvus/python/uploads/preset/images/test/basset/n02088238_4152.JPEG"
    
    if not os.path.exists(test_image_path):
        logger.error(f"Test image not found: {test_image_path}")
        test_image_path = input("Please enter the path of the test image: ")
    
    # 调用函数测试
    logger.info(f"Using test image: {test_image_path}")
    results = get_similar_image_paths(test_image_path, milvus_client, extractor, collection_name, top_k=10)
    
    # 打印结果
    logger.info(f"Found {len(results)} similar images")
    for i, img_info in enumerate(results, 1):
        logger.info(f"{i}. Similar image rel_path: {img_info['path']}")
        logger.info(f"   Similar image abs_path: {os.path.join(os.environ.get('TRAIN_IMAGE_ROOT_PATH'), img_info['path'])}")
        logger.info(f"   Distance: {img_info['distance']:.4f}")
        logger.info(f"   Similarity: {img_info['similarity']:.4f}\n")
        
   
