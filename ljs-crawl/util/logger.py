import logging
from pathlib import Path
def config_logger(logger_name:str,logfile_path:str):
    p = Path(logfile_path)
    if not p.parent.exists():
        p.parent.mkdir(parents=True)
    # 设置日志输出
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(levelname)s][%(asctime)s] : %(message)s')
    file_handler = logging.FileHandler(logfile_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger