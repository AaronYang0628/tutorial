"""
Document Processor Service 客户端

提供完整的 API 接口调用封装，支持批量文档处理、Iterator 分页获取等功能
"""

from typing import List, Dict, Optional, Any, Iterator
import time


class DocumentProcessorClient:
    """Document Processor 服务客户端

    封装所有 API 端点，提供便捷的文档处理接口
    """

    def __init__(
        self,
        service_url: str = "http://localhost:8010",
        timeout: int = 300
    ):
        """
        初始化 Document Processor 客户端

        Args:
            service_url: Document Processor 服务地址
            timeout: 请求超时时间（秒），默认 300 秒
        """
        try:
            import httpx
        except ImportError:
            raise ImportError("Please install httpx: pip install httpx")

        self.service_url = service_url.rstrip('/')
        self.client = httpx.Client(base_url=self.service_url, timeout=timeout)
        self._version: Optional[str] = None

        # 验证服务连接
        self._verify_service()

    def _verify_service(self):
        """验证服务连接并获取服务信息"""
        try:
            response = self.client.get("/health")
            response.raise_for_status()
            data = response.json()

            self._version = data.get("version", "unknown")
            print(f"✓ Connected to Document Processor service")
            print(f"  Service URL: {self.service_url}")
            print(f"  Version: {self._version}")

        except Exception as e:
            raise ConnectionError(
                f"Cannot connect to Document Processor service at {self.service_url}: {e}"
            )

    def submit_batch(
        self,
        files: List[Dict[str, Any]],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        提交批处理任务

        Args:
            files: 文件列表，每个文件包含 uri 和可选的 metadata
                例如: [{"uri": "s3://bucket/file.pdf", "metadata": {"title": "Doc"}}]
            config: 处理配置，可选参数包括:
                - chunk_size: 分块大小 (默认 512)
                - chunk_overlap: 分块重叠 (默认 50)
                - chunking_strategy: 分块策略 (semantic/fixed/paragraph)
                - timeout_per_file: 单文件超时时间

        Returns:
            包含 iterator_id, total_files, status 的字典
        """
        if not files:
            raise ValueError("Files list cannot be empty")

        payload = {"files": files}
        if config:
            payload["config"] = config

        try:
            response = self.client.post("/process/batch", json=payload)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            raise RuntimeError(f"Failed to submit batch processing: {e}")

    def get_status(self, iterator_id: str) -> Dict[str, Any]:
        """
        查询处理状态

        Args:
            iterator_id: Iterator ID

        Returns:
            状态信息，包含:
                - iterator_id: Iterator ID
                - status: 状态 (processing/completed/failed)
                - total_files: 总文件数
                - processed_files: 已处理文件数
                - failed_files: 失败文件数
                - total_chunks: 总块数
                - created_at: 创建时间
                - completed_at: 完成时间（如果已完成）
        """
        try:
            response = self.client.get(f"/status/{iterator_id}")
            response.raise_for_status()
            return response.json()

        except Exception as e:
            raise RuntimeError(f"Failed to get status for {iterator_id}: {e}")

    def get_next(
        self,
        iterator_id: str,
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        获取下一批处理结果

        Args:
            iterator_id: Iterator ID
            batch_size: 每批返回的 chunk 数量，默认 50

        Returns:
            包含 iterator_id, has_more, chunks 的字典
        """
        try:
            response = self.client.get(
                f"/process/batch/{iterator_id}/next",
                params={"batch_size": batch_size}
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            raise RuntimeError(f"Failed to get next batch for {iterator_id}: {e}")

    def reset(self, iterator_id: str) -> Dict[str, Any]:
        """
        重置 Iterator 到起始位置

        Args:
            iterator_id: Iterator ID

        Returns:
            重置结果，包含 iterator_id, status, message
        """
        try:
            response = self.client.post(f"/process/batch/{iterator_id}/reset")
            response.raise_for_status()
            return response.json()

        except Exception as e:
            raise RuntimeError(f"Failed to reset iterator {iterator_id}: {e}")

    def delete(self, iterator_id: str) -> Dict[str, Any]:
        """
        删除 Iterator，释放资源

        Args:
            iterator_id: Iterator ID

        Returns:
            删除结果，包含 status, message
        """
        try:
            response = self.client.delete(f"/process/batch/{iterator_id}")
            response.raise_for_status()
            return response.json()

        except Exception as e:
            raise RuntimeError(f"Failed to delete iterator {iterator_id}: {e}")

    def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            健康状态信息
        """
        try:
            response = self.client.get("/health")
            response.raise_for_status()
            return response.json()

        except Exception as e:
            raise RuntimeError(f"Health check failed: {e}")

    def get_formats(self) -> Dict[str, Any]:
        """
        获取支持的文件格式

        Returns:
            支持的文件格式列表
        """
        try:
            response = self.client.get("/formats")
            response.raise_for_status()
            return response.json()

        except Exception as e:
            raise RuntimeError(f"Failed to get supported formats: {e}")

    def wait_for_completion(
        self,
        iterator_id: str,
        poll_interval: int = 2,
        max_wait: int = 300
    ) -> Dict[str, Any]:
        """
        等待处理完成

        Args:
            iterator_id: Iterator ID
            poll_interval: 轮询间隔（秒），默认 2 秒
            max_wait: 最大等待时间（秒），默认 300 秒

        Returns:
            最终状态信息

        Raises:
            TimeoutError: 超过最大等待时间
            RuntimeError: 处理失败
        """
        start_time = time.time()

        while True:
            status = self.get_status(iterator_id)
            current_status = status.get("status")

            if current_status == "completed":
                return status
            elif current_status == "failed":
                raise RuntimeError(f"Processing failed for iterator {iterator_id}")

            elapsed = time.time() - start_time
            if elapsed > max_wait:
                raise TimeoutError(
                    f"Processing timeout after {elapsed:.1f} seconds for iterator {iterator_id}"
                )

            time.sleep(poll_interval)

    def iter_all_chunks(
        self,
        iterator_id: str,
        batch_size: int = 50,
        wait_for_completion: bool = True
    ) -> Iterator[Dict[str, Any]]:
        """
        迭代获取所有 chunks

        Args:
            iterator_id: Iterator ID
            batch_size: 每批获取的 chunk 数量
            wait_for_completion: 是否等待处理完成

        Yields:
            每个 chunk 的字典
        """
        if wait_for_completion:
            self.wait_for_completion(iterator_id)

        has_more = True
        while has_more:
            result = self.get_next(iterator_id, batch_size=batch_size)
            chunks = result.get("chunks", [])
            has_more = result.get("has_more", False)

            for chunk in chunks:
                yield chunk

    @property
    def version(self) -> str:
        """返回服务版本"""
        return self._version or "unknown"

    def close(self):
        """关闭 HTTP 客户端"""
        self.client.close()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
