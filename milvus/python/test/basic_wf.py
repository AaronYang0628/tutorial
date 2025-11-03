import sys
import os
import time
from typing import Dict, List
from sdk.document_processor_client import DocumentProcessorClient

def test_basic_workflow():
    """测试基本工作流程：提交 -> 等待 -> 获取结果 -> 清理"""
    test_name = "示例 2: 基本工作流程"
    start_time = time.time()

    try:
        print("\n" + "=" * 60)
        print(test_name)
        print("=" * 60)

        with DocumentProcessorClient(service_url="http://localhost:8010") as client:
            # 1. 提交批处理任务
            print("\n步骤 1: 提交批处理任务")
            files = [
                {
                    "uri": "s3://document-processor/test.md",
                    "metadata": {
                        "title": "测试文档",
                        "author": "RAG Team"
                    }
                }
            ]
            config = {
                "chunk_size": 512,
                "chunk_overlap": 50,
                "chunking_strategy": "paragraph"
            }

            result = client.submit_batch(files=files, config=config)
            iterator_id = result.get("iterator_id")
            print(f"  Iterator ID: {iterator_id}")
            print(f"  总文件数: {result.get('total_files')}")

            # 2. 查询状态
            print("\n步骤 2: 查询处理状态")
            status = client.get_status(iterator_id)
            print(f"  状态: {status.get('status')}")
            print(f"  已处理: {status.get('processed_files', 0)}/{status.get('total_files')}")

            # 3. 等待完成
            print("\n步骤 3: 等待处理完成...")
            final_status = client.wait_for_completion(iterator_id, poll_interval=1)
            print(f"  最终状态: {final_status.get('status')}")
            print(f"  总块数: {final_status.get('total_chunks')}")
            print(f"  失败文件: {final_status.get('failed_files', 0)}")

            # 4. 获取结果（分批）
            print("\n步骤 4: 获取处理结果")
            first_batch = client.get_next(iterator_id, batch_size=5)
            chunks = first_batch.get("chunks", [])
            print(f"  第一批获取了 {len(chunks)} 个 chunks")
            print(f"  还有更多: {first_batch.get('has_more')}")

            if chunks:
                print(f"\n  第一个 chunk 示例:")
                chunk = chunks[0]
                print(f"    ID: {chunk.get('chunk_id')}")
                print(f"    文件: {chunk.get('file_uri')}")
                print(f"    文本长度: {len(chunk.get('text', ''))}")
                print(f"    索引: {chunk.get('chunk_index')}")
                print(f"    文本预览: {chunk.get('text', '')[:100]}...")

            # 5. 清理资源
            print("\n步骤 5: 清理资源")
            delete_result = client.delete(iterator_id)
            print(f"  {delete_result.get('message')}")

        test_result.add_result(test_name, "success", time.time() - start_time)

    except Exception as e:
        test_result.add_result(test_name, "failed", time.time() - start_time, str(e))
        raise