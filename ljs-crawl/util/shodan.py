'''
使用shodan查询ip的CIDR块其余活跃IP，以及端口开放信息
'''
import ipaddress
import shodan

from cachetools import cached,LRUCache

class SHODAN:
    def __init__(self,apikey:str,subnet_mask:str=None,provider:str=None):
        self.subnet_mask=subnet_mask
        self.api=shodan.Shodan(apikey)
        self.provider=provider

    def get_cidr_block(self,ip_address):
        # 创建网络对象
        network = ipaddress.IPv4Network(ip_address + '/' + self.subnet_mask, strict=False)
        # 获取CIDR块
        cidr_block = str(network.network_address) + '/' + str(network.prefixlen)

        return cidr_block
    
    @cached(LRUCache(maxsize=1024))
    def __search_shodan(self,cidr_block:str):
        ip_set = set()
        try:
            result = self.api.search('net:'+cidr_block)
            for data in result['matches']:
                if data.get('cloud') != None and data['cloud'].get('provider') == self.provider:
                    ip_set.add(data['ip_str'])
            return ip_set
        except Exception as e:
            print(e)
            return None

    def expand_ip(self,ip:str):
        cidr_block = self.get_cidr_block(ip)
        try:
            ips = self.__search_shodan(cidr_block)
            if ips != None:
                return list(ips)
            else:
                return None
        except Exception as e:
            print(e)
            return None
    
    def get_ip_info(self,ip:str):
        try:
            info = self.api.host(ip)
        except Exception as e:
            return {'org':'-','ports':'-'}
        datas = info['data']
        org = info['org']
        if org is None:
            org = '-'
        ports_info = []
        for data in datas:
            port = data['port']
            trnasport = data['transport']
            product = data.get('product','-')
            os = data['os']
            if product is None:
                product = '-'
            if os is None:
                os = '-'
            ports_info.append(f'{port}^{trnasport}^{product}^{os}')
        return {'org':info.get('org'),'ports':'|'.join(ports_info)}
                
            # return {'org':info.get('org'),'ports':'|'.join()}

    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cache.clear()
        return False