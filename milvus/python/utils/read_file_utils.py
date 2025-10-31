
import os
from glob import glob
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger_util import setup_logging

# 在模块加载时设置默认日志器
logger = setup_logging('read.file.util')

def read_markdown(path, recursive=True):
    logger.info(f"Going to read markdown files from: {path}")
    raw_text_lines = []
    for file_path in glob(path, recursive=recursive):
        with open(file_path, "r", encoding="utf-8") as file:
            logger.info(f"processing file at {file_path}")
            file_text = file.read()
        raw_text_lines += file_text.split("# ")
    return raw_text_lines