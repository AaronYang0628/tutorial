import time
import os
import sys
from tqdm import tqdm
from pymilvus import MilvusClient
from openai import OpenAI
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.embedding_utils import embed_text
from utils.read_file_utils import read_markdown
from utils.env_utils import load_env_config
from utils.logger_util import setup_logging

# 在模块加载时设置默认日志器
logger = setup_logging('update.rag')

def update_rag_collection(mode, doc_path, milvus_client, openai_client, collection_name,
                         embedding_dim, embedding_model):
    """
    更新RAG向量库
    
    Args:
        mode: 操作模式 ('create' 或 'upgrade')
        doc_path: 文档路径
        milvus_client: Milvus客户端实例
        openai_client: OpenAI客户端实例
        collection_name: 集合名称
        embedding_dim: 嵌入维度
        embedding_model: 嵌入模型
        logger: 日志记录器（可选）
    
    Returns:
        dict: 包含操作结果的字典
    """
    
    result = {"status": "success", "message": "", "flush_time": 0}
    
    try:
        if mode == "create":
            cooked_data = []
            
            # 读取文档
            raw_text_lines = read_markdown(doc_path)
            
            # 如果集合已存在则删除
            if milvus_client.has_collection(collection_name):
                milvus_client.drop_collection(collection_name)
                logger.info(f"Dropped existing collection {collection_name}")
                result["message"] += f"Dropped existing collection {collection_name}. "
            
            # 创建新集合
            milvus_client.create_collection(
                collection_name=collection_name,
                dimension=embedding_dim,
                metric_type="IP",
                consistency_level="Bounded",
            )
            
            logger.info(f"Created collection {collection_name}")
            result["message"] += f"Created collection {collection_name}. "
            
            # 生成嵌入并插入数据
            for i, line in enumerate(tqdm(raw_text_lines, desc="Creating embeddings")):
                cooked_data.append({
                    "id": i, 
                    "vector": embed_text(openai_client, line, embedding_model), 
                    "text": line
                })
            
            milvus_client.insert(collection_name=collection_name, data=cooked_data)
            result["message"] += f"Inserted {len(cooked_data)} documents."
            
        elif mode == "upgrade":
            if milvus_client.has_collection(collection_name):
                cooked_data = []
                
                # 读取文档
                raw_text_lines = read_markdown(doc_path)
                
                # 获取当前最大ID
                max_id = 0
                try:
                    # 尝试获取现有文档的最大ID
                    query_res = milvus_client.query(
                        collection_name=collection_name,
                        filter="",
                        output_fields=["id"],
                        limit=1,
                        offset=0,
                        consistency_level="Strong"
                    )
                    if query_res:
                        max_id = max([res["id"] for res in query_res])
                except Exception as e:
                    log(f"Failed to get max ID, starting from 0: {str(e)}")
                
                # 生成嵌入并插入新数据
                for i, line in enumerate(tqdm(raw_text_lines, desc="Creating embeddings")):
                    cooked_data.append({
                        "id": max_id + i + 1,  # 避免ID冲突
                        "vector": embed_text(openai_client, line, embedding_model), 
                        "text": line
                    })
                
                milvus_client.insert(collection_name=collection_name, data=cooked_data)
                result["message"] += f"Appended {len(cooked_data)} documents."
            else:
                raise ValueError(f"Collection {collection_name} does not exist")
        else:
            raise ValueError(f"Unknown collection update mode: {mode}")
        
        # 刷新数据
        logger.info("Start to flush")
        start_flush = time.time()
        milvus_client.flush(collection_name)
        end_flush = time.time()
        flush_time = round(end_flush - start_flush, 4)
        result["flush_time"] = flush_time
        result["message"] += f" Flush completed in {flush_time} seconds."
        logger.info(f"Flush completed in {flush_time} seconds")
        
        return result
        
    except Exception as e:
        log(f"Error during update: {str(e)}")
        raise


# 以下为直接运行此脚本时的示例代码
if __name__ == "__main__":
    # 加载环境变量
    load_env_config("../.env")
    
    # 加载配置
    milvus_uri = os.environ.get("MILVUS_URI", "http://localhost:19530")
    token = os.environ.get("MILVUS_TOKEN", "")
    collection_name = os.environ.get("QA_COLLECTION_NAME", "default_collection")
    embedding_dim = int(os.environ.get("EMBEDDING_DIM", "1024"))
    embedding_model = os.environ.get("EMBEDDING_MODEL", "text-embedding-v4")
    doc_path = os.environ.get("EXT_DOC_PATH", "milvus_docs/en/faq/*.md")
    
    # 初始化客户端
    openai_client = OpenAI(
        api_key=os.environ.get("TONGYI_API_KEY", os.environ.get("OPENAI_API_KEY", "")),
        base_url=os.environ.get("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    )
    
    milvus_client = MilvusClient(uri=milvus_uri, token=token)
    logger.info(f"Connected to DB: {milvus_uri} successfully")
    
    # 执行更新
    result = update_rag_collection(
        mode="create",
        doc_path=doc_path,
        milvus_client=milvus_client,
        openai_client=openai_client,
        collection_name=collection_name,
        embedding_dim=embedding_dim,
        embedding_model=embedding_model
    )
    
    logger.info(f"Update result: {result}")

