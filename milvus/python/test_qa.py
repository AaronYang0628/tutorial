from dotenv import load_dotenv
import os
from openai import OpenAI
from pymilvus import MilvusClient
from ragQA.qa_rag import QASystem

def main():
    # 加载环境变量
    load_dotenv()
    
    # 初始化 OpenAI 客户端
    openai_client = OpenAI(
        api_key=os.environ.get("TONGYI_API_KEY", os.environ.get("OPENAI_API_KEY", "")),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    
    # 初始化 Milvus 客户端
    milvus_uri = os.environ.get("MILVUS_URI", "http://localhost:19530")
    token = os.environ.get("MILVUS_TOKEN", "")
    milvus_client = MilvusClient(uri=milvus_uri, token=token)
    
    # 设置集合名称
    collection_name = os.environ.get("MILVUS_COLLECTION", "default_collection")
    
    # 初始化QA系统
    qa_system = QASystem(openai_client)
    
    # 测试问题
    questions = [
        "How is data stored in milvus?",
        "What are the main features of milvus?",
        # 添加更多问题...
    ]
    
    # 测试每个问题
    for question in questions:
        print(f"\nQuestion: {question}")
        print("-" * 50)
        
        try:
            # 获取答案和源文档
            answer, sources = qa_system.answer_question(
                milvus_client, 
                collection_name, 
                question,
                return_sources=True
            )
            
            # 打印答案
            print("Answer:")
            print(answer)
            
            # 打印源文档和相似度分数
            print("\nSources:")
            for text, score in sources:
                print(f"Score: {score:.4f}")
                print(f"Text: {text[:200]}...")  # 只显示前200个字符
                print("-" * 30)
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()