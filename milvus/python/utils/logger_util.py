import logging

def setup_logging(logger_name: str = 'app', level: int = logging.INFO) -> logging.Logger:
    """
    设置全局日志配置，确保日志输出到控制台
    
    Args:
        logger_name: 日志器名称
        level: 日志级别
        
    Returns:
        配置好的日志器实例
    """
    # 获取或创建日志器
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # 检查是否已有处理器，如果没有则添加
    if not logger.handlers:
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # 设置日志格式
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        
        # 添加处理器到logger
        logger.addHandler(console_handler)
    
    return logger
