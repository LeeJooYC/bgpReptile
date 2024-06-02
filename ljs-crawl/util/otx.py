'''
使用otx查询ip的passive dns信息
'''
import timeout_decorator

from OTXv2 import OTXv2,RetryError
from OTXv2 import IndicatorTypes
from cachetools import cached,LRUCache


class OTX:
    def __init__(self,key:str,time_out:int=3):
        self.otx = OTXv2(key)
        self.time_out = time_out
    
    @cached(LRUCache(maxsize=1024))
    def get_ip_passive_dns(self,ip:str):
        @timeout_decorator.timeout(self.time_out)
        def __get_ip_passive_dns(ip:str):
            res = self.otx.get_indicator_details_by_section(IndicatorTypes.IPv4, ip,'passive_dns')
            res = [item['hostname'] for item in res['passive_dns']]
            return res
        try:
            res = __get_ip_passive_dns(ip)
        except (RetryError,timeout_decorator.TimeoutError) as e:
            return []
        return res
    
    def test(self,ip:str,section:str):
        res = self.otx.get_indicator_details_by_section(IndicatorTypes.IPv4, ip,section)
        return res