import json
import os
import sys
from pymilvus import MilvusClient
from openai import OpenAI

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.embedding_utils import embed_text
from utils.env_utils import load_env_config
from utils.logger_util import setup_logging

# 在模块加载时设置默认日志器
logger = setup_logging('qa.rag')

def answer_question(question, milvus_client, openai_client, collection_name, embedding_model="text-embedding-v4", 
                    grab_top_n_res=5, llm_model="gpt-3.5-turbo"):
    """
    回答用户问题
    
    Args:
        question: 用户问题
        milvus_client: Milvus客户端实例
        openai_client: OpenAI客户端实例
        collection_name: Milvus集合名称
        embedding_model: 嵌入模型名称
        grab_top_n_res: 检索结果数量
        llm_model: LLM模型名称
    
    Returns:
        dict: 包含回答和检索源的字典
    """
    logger.info(f"Answering question: {question}")
    logger.info(f"Using collection: {collection_name}")

    # 搜索相似文本
    search_res = milvus_client.search(
        collection_name=collection_name,
        data=[
            embed_text(openai_client, question, embedding_model)
        ],  
        limit=grab_top_n_res, 
        search_params={"metric_type": "IP", "params": {}}, 
        output_fields=["text"], 
    )

    # 处理检索结果
    retrieved_lines_with_distances = [
        (res["entity"]["text"], res["distance"]) for res in search_res[0]
    ]

    # 构建上下文
    context = "\n".join(
        [line_with_distance[0] for line_with_distance in retrieved_lines_with_distances]
    )

    # 定义提示词
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

    # 获取LLM回答
    response = openai_client.chat.completions.create(
        model=llm_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ],
    )

    return {
        "response": response.choices[0].message.content,
        "sources": retrieved_lines_with_distances
    }


# 以下为直接运行此脚本时的示例代码
if __name__ == "__main__":
    load_env_config("../.env")
    
    # 加载配置
    milvus_uri = os.environ.get("MILVUS_URI", "http://localhost:19530")
    token = os.environ.get("MILVUS_TOKEN", "")
    collection_name = os.environ.get("QA_COLLECTION_NAME", "default_collection")
    embedding_model = os.environ.get("EMBEDDING_MODEL", "")
    grab_top_n_res = int(os.environ.get("GRABE_TOP_N_RES", "5"))
    llm_model = os.environ.get("LLM_MODEL", "gpt-3.5-turbo")

    # 初始化客户端
    openai_client = OpenAI(
        api_key=os.environ.get("TONGYI_API_KEY", os.environ.get("OPENAI_API_KEY", "")),
        base_url=os.environ.get("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    )

    milvus_client = MilvusClient(uri=milvus_uri, token=token)

    logger.info(f"Connected to DB: {milvus_uri} successfully")

    if milvus_client.has_collection(collection_name):
        question = "How is data stored in milvus?"
        result = answer_question(
            question=question,
            milvus_client=milvus_client,
            openai_client=openai_client,
            collection_name=collection_name,
            embedding_model=embedding_model,
            grab_top_n_res=grab_top_n_res,
            llm_model=llm_model
        )
        
        print(json.dumps(result["sources"], indent=4))
        print(result["response"])
    else:
        print(f"Cannot find collection {collection_name} in milvus: {milvus_uri}")