
import os
from glob import glob
import sys
import time
from typing import List, Dict, Union
from urllib.parse import urlparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger_util import setup_logging
from sdk.document_processor_client import DocumentProcessorClient

# 在模块加载时设置默认日志器
logger = setup_logging('read.file.util')

def _is_s3_path(path: str) -> bool:
    """
    判断路径是否为S3路径
    """
    return path.startswith('s3://') or path.startswith('S3://')

def _process_s3_path(path: str) -> List[Dict]:
    """
    处理S3路径，返回文件列表
    """
    # 如果是单个S3文件路径
    files_to_process = [{
        "uri": path,
        "metadata": {
            "source": path,
            "filename": os.path.basename(urlparse(path).path)
        }
    }]
    return files_to_process

def _process_local_path(path: str, recursive: bool) -> List[Dict]:
    """
    处理本地文件路径，返回文件列表
    """
    all_files = []
    if os.path.isfile(path):
        all_files = [path]
    else:
        all_files = [f for f in glob(path, recursive=recursive)]
    
    if not all_files:
        logger.warning(f"No local files found in {path}")
        return []
    
    files_to_process = []
    for file_path in all_files:
        abs_path = os.path.abspath(file_path)
        files_to_process.append({
            "uri": f"file://{abs_path}",
            "metadata": {
                "source": abs_path,
                "filename": os.path.basename(abs_path)
            }
        })
    return files_to_process

def process_documents(path: str, recursive: bool = True, chunk_size: int = 512, 
                     chunk_overlap: int = 50, chunking_strategy: str = "paragraph") -> List[Dict]:
    """
    处理指定路径下的文档文件（支持本地文件和S3路径）
    
    Args:
        path: 文件路径（支持本地文件路径或S3路径 s3://bucket/path/to/file）
        recursive: 是否递归处理子目录（仅对本地文件有效）
        chunk_size: 文本块大小
        chunk_overlap: 文本块重叠大小
        chunking_strategy: 分块策略
    
    Returns:
        List[Dict]: 包含处理后的文本块列表
    """
    logger.info(f"Processing documents from: {path}")
    
    # 根据路径类型获取文件列表
    if _is_s3_path(path):
        files_to_process = _process_s3_path(path)
    else:
        files_to_process = _process_local_path(path, recursive)
    
    if not files_to_process:
        logger.warning(f"No files found to process at {path}")
        return []
    
    # 配置处理参数
    config = {
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "chunking_strategy": chunking_strategy
    }
    
    all_chunks = []
    try:
        with DocumentProcessorClient(os.environ.get("DOC_PROCESSING_URL", 'http://10.200.92.11:32010')) as client:
            # 提交批处理任务
            result = client.submit_batch(files=files_to_process, config=config)
            iterator_id = result.get("iterator_id")
            logger.info(f"Submitted batch job with iterator_id: {iterator_id}")
            
            # 等待处理完成
            final_status = client.wait_for_completion(iterator_id, poll_interval=1, max_wait=600)
            if final_status.get("status") != "completed":
                logger.error(f"Processing failed with status: {final_status.get('status')}")
                return []
            
            # 获取所有结果
            while True:
                batch = client.get_next(iterator_id, batch_size=100)
                chunks = batch.get("chunks", [])
                all_chunks.extend(chunks)
                
                if not batch.get("has_more"):
                    break
            
            # 清理资源
            client.delete(iterator_id)
            
    except Exception as e:
        logger.error(f"Error processing documents: {str(e)}")
        return []
    
    logger.info(f"Successfully processed {len(all_chunks)} chunks from {len(files_to_process)} files")
    return all_chunks

def read_markdown(path: str, recursive: bool = True) -> List[str]:
    """
    保持向后兼容的markdown读取函数
    """
    logger.info("Using new document processor for markdown files")
    chunks = process_documents(path, recursive=recursive)
    print(chunks)
    return [chunk["text"] for chunk in chunks if chunk.get("text")]

