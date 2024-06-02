#import logging
import os
import time
import traceback

from logging import Logger
from .logger import config_logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class Spider:
    def __init__(self,logger_name:str,logfile_path:str):
        # 设置日志输出
        # self.logger = logging.getLogger(logger_name)
        # self.logger.setLevel(logging.INFO)
        # formatter = logging.Formatter('[%(levelname)s][%(asctime)s] : %(message)s')
        # file_handler = logging.FileHandler(logfile_path)
        # file_handler.setLevel(logging.DEBUG)
        # file_handler.setFormatter(formatter)
        # console_handler = logging.StreamHandler()
        # console_handler.setLevel(logging.INFO)
        # console_handler.setFormatter(formatter)
        # self.logger.addHandler(file_handler)
        # self.logger.addHandler(console_handler)
        self.logger = config_logger(logger_name,logfile_path)

class Driver:
    def __init__(self,debug:bool=False,logger:Logger=None):
        self.chrome_options = Options()
        #设置无头模式
        if not debug:
            self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.chrome_options.add_argument("--start-maximized")
        self.chrome_options.add_argument("--log-level=3")
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument("user-agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.199 Safari/537.36'")
        #防止网站检测1
        self.chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        self.logger = logger

    def __enter__(self):
        # 无头模式打开Chrome
        self.driver = webdriver.Chrome(options=self.chrome_options)

        #防止网站检测2
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
            })
        """
        })

        return self.driver

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # 若父文件夹不存在error文件夹则创建
            if not os.path.exists('error'):
                os.mkdir('error')
            current_path = os.path.dirname(os.path.realpath(__file__))
            parent_path = os.path.dirname(current_path)
            self.driver.save_screenshot(f'{parent_path}/error/error_{time.strftime("%Y%m%d_%H%M%S", time.localtime()) }.png')
            # 保存网页源码
            with open(f'{parent_path}/error/error_{time.strftime("%Y%m%d_%H%M%S", time.localtime()) }.html','w',encoding='utf-8') as f:
                f.write(self.driver.page_source)
            if self.logger is not None:
                tb_str = ''.join(traceback.format_tb(exc_tb))
                self.logger.error(f"An exception occurred: {exc_val}\n{tb_str}")
        if self.driver is not None:
            self.driver.quit()
        
        return False
        