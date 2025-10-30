import os
from typing import Optional
import logging
from dotenv import load_dotenv

from utils.logger_util import setup_logging

# 在模块加载时设置默认日志器
logger = setup_logging('env.util')

def load_env_config(env_path: Optional[str] = None) -> None:
    logger.info(f"Loading environment variables from {env_path}")
    """
    根据条件加载环境变量配置
    
    Args:
        env_path: .env文件的路径，如果为None，则使用默认路径 '.env'
    """
    # 确定.env文件路径
    if env_path is None:
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    
    # 检查文件是否存在
    if not os.path.exists(env_path):
        logger.info(f"No .env file found at {env_path}, using system environment variables")
        return
        
    # 保存加载前的环境变量键列表
    original_env_keys = set(os.environ.keys())
    
    # 临时加载.env来检查MODE
    load_dotenv(env_path, override=True)
    mode = os.getenv('MODE')
    
    if mode != 'local':
        # 如果MODE不是local，恢复原始环境变量
        for key in list(os.environ.keys()):
            if key in os.environ:
                del os.environ[key]
        logger.info("MODE is not 'local', using system environment variables")
        return
        
    # 如果MODE是local，保持.env文件的环境变量
    logger.info(f"Using local configuration from {env_path}")
    
    # 找出从.env文件加载的新变量
    env_file_vars = {}
    for key in os.environ.keys():
        # 如果是新添加的变量或者值被覆盖了，认为是从.env文件加载的
        env_file_vars[key] = os.environ[key]
    
    logger.info("Loaded environment variables from .env file:")
    for key, value in env_file_vars.items():
        logger.info(f"{key}: {value}")
