import asyncio
import aiodns
from cachetools import cached,LRUCache

class DNSQUERY:
    def __init__(self,nameservers:list[str],timeout:int=2,logger=None):
        self.nameservers = nameservers
        self.timeout = timeout
        self.ip_set = set()
        self.cname_set = set()
        self.lock = asyncio.Lock()
        self.logger = logger

    async def __do_qurey(self, domain:str,server:str,type:str='A'):
        loop = asyncio.get_event_loop()
        resolver = aiodns.DNSResolver(loop=loop, nameservers=[server])
        try:
            result = await asyncio.wait_for(resolver.query(domain, type),timeout=self.timeout)
            async with self.lock:
                if type == 'CNAME':
                    if isinstance(result,list):
                        for result in result:
                            self.cname_set.add(result.cname)
                    else:
                        self.cname_set.add(result.cname)
                else:
                    if isinstance(result,list):
                        for result in result:
                            self.ip_set.add(result.host)
                    else:
                        self.ip_set.add(result.host)
        except Exception as e:
            pass

    async def run(self, domain,type:str='A'):
        tasks = []
        for server in self.nameservers:
            tasks.append(self.__do_qurey(domain,server,type))
        await asyncio.gather(*tasks)

    @cached(LRUCache(maxsize=1024))
    def query_ip(self, domain:str):
        self.ip_set.clear()
        asyncio.run(self.run(domain))
        return list(self.ip_set)

    @cached(LRUCache(maxsize=1024))
    def query_cname(self,domain:str):
        self.cname_set.clear()
        asyncio.run(self.run(domain,'CNAME'))
        return list(self.cname_set)