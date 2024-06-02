import json
import re
import time

from conf.aliyun import dns_server
# from multiprocessing import Queue,Manager,Lock,Pool
from concurrent.futures import ThreadPoolExecutor,as_completed
from queue import Queue
from threading import Lock
from tqdm import tqdm
from typing import Callable as function
from util.dns import DNSQUERY
from util.env import LOAD_ENV,GET_ENV
from util.logger import config_logger
from util.otx import OTX
from util.shodan import SHODAN


class ALIYUNIP: # 6-10s
    '''
    云服务节点扩展探测模块
    '''
    def __init__(self,OTX_KEY:str,SHODAN_KEY:str,dns_queryer:DNSQUERY,logger=None):
        self.otx = OTX(OTX_KEY)
        provider = 'Google'
        subnet_mask='255.255.255.0'
        self.shodan = SHODAN(SHODAN_KEY,subnet_mask,provider)
        if logger is not None:
            self.logger = logger
        self.dns_queryer = dns_queryer

    def otx_query(self,ips:list[str],feedback:function=None):
        # 1. 查询所有ip，得到ip的passive dns信息
        ip_passive_dns = []
        for ip in ips:
            ip_passive_dns += self.otx.get_ip_passive_dns(ip)
            time.sleep(0.1)
        if feedback is not None and len(ip_passive_dns) > 0:
            feedback(ip_passive_dns)
    
    def shodan_query(self,ip:str):
        cidr_ips = self.shodan.expand_ip(ip)
        if cidr_ips is not None:
            return cidr_ips
        else :
            return []

    def ip_query(self,domain:str):
        # 查询domain的ip
        ips = self.dns_queryer.query_ip(domain)
        return ips
    
    def run(self,domain:str,feedback:function=None):
        try:
            # 1. DNS解析IP
            ips = self.ip_query(domain)
            # 2. shodan扩展
            expand_ips =set()
            for ip in ips:
                cidr_ips = self.shodan_query(ip)
                if len(cidr_ips) > 0:
                    expand_ips.update(cidr_ips)
            # 3. otx查询历史域名
            self.otx_query(expand_ips,feedback)
            return ips
        except Exception as e:
            if self.logger is not None:
                self.logger.error(f'Error in processing {domain}, error:{e}')
            raise e
        return []

class ALIYUNDOMAIN:
    '''
    云服务域名规则循环匹配模块
    '''
    def __init__(self,rules:dict,dns_queryer:DNSQUERY,logger=None):
        self.rules = {re.compile(rule) : rules[rule] for rule in rules}
        self.dns_queryer = dns_queryer
        if logger is not None:
            self.logger = logger
    
    def cname_query(self,domain:str,feedback:function=None):
        cnames = self.dns_queryer.query_cname(domain)
        if feedback is not None and len(cnames) > 0:
            feedback(cnames)
        return cnames

    def match(self,domain:str):
        '''
        @return: (bool, service class or None)
        '''
        for rule in self.rules:
            if rule.match(domain):
                # 命中域名规则
                return True,self.rules[rule]
        
        return False,None

    def run(self,domain:str,feedback:function=None):
        try:
            # 1. 匹配域名规则
            is_aliyun,service = self.match(domain)
            if is_aliyun is True:
                return service
            else:
                # 2. 查询cname
                cnames = self.cname_query(domain,feedback)
        except Exception as e:
            if self.logger is not None:
                self.logger.error(f'Error in processing {domain}, error:{e}')
            raise e
        return None

class ALIYUNMAIN:
    def __init__(self,nameservers:list, class_ids:list[int]):
        # 加载KEY
        LOAD_ENV()
        self.otx_key = GET_ENV('OTX_KEY')
        self.shodan_key = GET_ENV('SHODAN_KEY')
        # 初始化种子域名
        self.domain_queue = Queue()
        self.queue_lock = Lock()
        self.__load_seed()
        # 初始化日志
        self.logger = config_logger('Google','./log/google.log')
        self.evaluated_domain = set()
        self.added_domain = set()
        self.dns_queryer = DNSQUERY(nameservers,logger=self.logger)
        self.ip_module = ALIYUNIP(self.otx_key,self.shodan_key,self.dns_queryer,self.logger)
        rules = self.__load_rules()
        self.domain_module = ALIYUNDOMAIN(rules,self.dns_queryer,self.logger)
        #self.result = dict()
        self.result = dict()
        self.ip_result = set()
        self.ip_result_class = dict()
        
        for class_id in class_ids:
            self.result[str(class_id)] = list()
            self.ip_result_class[str(class_id)] = set()

    def __load_seed(self):
        with open('google_seed_domains.json','r') as f:
            seed_domains = json.load(f)
        for domain in seed_domains:
            self.domain_queue.put(domain)
    
    @staticmethod
    def __load_rules():
        with open('google_rule_processed.json','r') as f:
            rules = json.load(f)
        return rules

    def feedback(self,data):
        ind = 0
        self.queue_lock.acquire()
        for d in data:
            if d in self.added_domain:
                ind += 1
                continue
            self.domain_queue.put(d)
            self.added_domain.add(d)
        self.queue_lock.release()
        if len(data)-ind > 0:
            self.logger.info(f'feedback {len(data) - ind} domains')
    
    def save_result(self):
        result_ip_class = {class_id: list(domains) for class_id,domains in self.ip_result_class.items()}
        result_ips = list(self.ip_result)
        result = {class_id: domains for class_id,domains in self.result.items()}
        with open('result_ip_class.json','w') as f:
            json.dump(result_ip_class,f,ensure_ascii=False,indent=4)
        with open('result_ips.json','w') as f:
            json.dump(result_ips,f,ensure_ascii=False,indent=4)
        with open('result.json','w') as f:
            json.dump(result,f,ensure_ascii=False,indent=4)
    def run(self):
        hit_domain=set()
        with tqdm() as bar:
            ind = 1
            hit = 0
            while not self.domain_queue.empty():
                bar.set_description(f'process {ind}, {self.domain_queue.qsize()} left')
                domain = self.domain_queue.get()
                if domain in self.evaluated_domain:
                    ind += 1
                    bar.update(1)
                    continue
                self.evaluated_domain.add(domain)
                services = self.domain_module.run(domain,self.feedback)
                if services is None:
                    ind += 1
                    bar.update(1)
                    continue
                else:
                    hit_domain.add(domain)
                    hit += 1
                ips = self.ip_module.run(domain,self.feedback)
                self.ip_result.update(ips)
                for service in services:
                    self.ip_result_class[service].update(ips)
                    tmp = {domain:ips}
                    self.result[service].append(tmp)
                bar.update(1)
                ind += 1
                self.save_result()

        with open('hit_domain.json','w') as f:
            json.dump(list(hit_domain),f,ensure_ascii=False,indent=4)

if __name__ == "__main__":
    class_ids = [0,1,2]
    main = ALIYUNMAIN(dns_server,class_ids)
    main.run()
            
            
