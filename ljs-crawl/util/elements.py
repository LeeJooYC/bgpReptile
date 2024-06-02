from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class get_elements_func:
    def __init__(self,logger=None):
        self.logger = logger

    def by_xpath(self,driver,xpath,time_out=5,log:bool=True):
        try:
            elements:list = WebDriverWait(driver, timeout=time_out).until(
                EC.presence_of_all_elements_located((By.XPATH, xpath))
            )
        except Exception as e:
            if self.logger is not None and log:
                self.logger.warning(f'exception occur, xpath: [{xpath}], url: [{driver.current_url}].')
            elements = []

        return elements

    def by_attr(self,driver,attr:str='class',prefix:str=None,tag:str='*',sub_node:str='',time_out=10,log:bool=True):
        '''
        根据属性内容前缀获取所有元素
        '''
        xpath = f"//{tag}[contains(@{attr}, \"{prefix}\")]"+sub_node
        elements = self.by_xpath(driver,xpath,time_out,log)
        return elements

    def by_text(self,driver,text:str,tag:str="*",contain:bool=False,time_out:int=10,log:bool=True):
        '''
        根据内容获取所有元素
        '''
        if contain:
            xpath=f"//{tag}[contains(text(),\"{text}\")]"
        else:
            xpath=f"//{tag}[text()=\"{text}\"]"
        elements = self.by_xpath(driver,xpath,time_out,log)
        return elements