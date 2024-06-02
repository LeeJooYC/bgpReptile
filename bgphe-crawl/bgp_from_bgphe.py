from tqdm import tqdm
import requests
import re
import socket
import pymysql
import ipaddress

def ipv42int(ip):
    ip_list = ip.split('.')
    cnt = 0
    for i in ip_list:
        cnt *= 256
        cnt += int(i)
    return cnt

class Trie:
    def __init__(self):
        self.root = {}

    def insert(self, ip, cidr_k):
        ip_num = str(bin(ipv42int(ip)))[2:].zfill(32)
        ip_bin = list(str(ip_num))
        current = self.root
        for i in range(cidr_k):
            if ip_bin[i] not in current:
                current[ip_bin[i]] = {}
            current = current[ip_bin[i]]


    def find(self, ip):
        ip_num = str(bin(ipv42int(ip)))[2:].zfill(32)
        ip_bin = list(str(ip_num))
        current = self.root
        cidr_k = 0
        for v in ip_bin:
            if v in current:
                cidr_k += 1
                current = current[v]
            else:
                return cidr_k
        return cidr_k

def is_valid_ip(ip):
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False

def bgphe_crawl(trie):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='usejydjq0078', port=3306, db='gcp')
    cur = conn.cursor()
    count = 0

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'}

    response = requests.get('https://bgp.he.net/search?search%5Bsearch%5D=google&commit=Search', headers=headers)
    page_content = response.text

    pattern_ip = r'<a href="[^"]+">([^<]+)</a>'
    pattern_region = r'title="([^"]+)" /></div></td>'
    # pattern = re.compile(pattern, re.IGNORECASE)
    # country_matches = pattern.findall(page_content)

    pos = 0
    res = []
    while True:
        bgn = page_content.find('<tr>', pos)
        nd = page_content.find('</tr>', bgn)
        if bgn == -1:
            break
        pos = nd

        subcontent = page_content[bgn:nd]
        if 'Google' not in subcontent:
            continue
        match_ip = re.search(pattern_ip, subcontent)
        match_region = re.search(pattern_region, subcontent)
        ip = None
        region = None
        if match_ip is not None:
            ip = subcontent[match_ip.regs[1][0]:match_ip.regs[1][1]]
        if match_region is not None:
            region = subcontent[match_region.regs[1][0]:match_region.regs[1][1]]
        if ip is not None and is_valid_ip(ip[:ip.find('/')]):
            res.append([ip, region])

    pbar = tqdm(total=len(res))
    pbar.set_description(f"Current number is {count}")

    for item in res:
        if '/' in item[0]:
            tmp = item[0].split('/')
            ip = tmp[0]
            cidr = int(tmp[1])
            ip_int = ipv42int(ip)
            if cidr < 24:
                for i in range(2 ** (24 - cidr)):
                    ip_tmp = ip_int + i * 256
                    ip_tmp = str(ipaddress.ip_address(ip_tmp))
                    a = trie.find(ip_tmp)

                    if trie.find(ip_tmp) < 24:
                        ip_tmp = f"{ip_tmp}/24"
                        try:
                            sql = "insert into target(ip, type, data_center, label) values (%s, %s, %s, %s)"
                            cur.execute(sql, (ip_tmp, 'prefix', item[1], False))
                            count += 1
                        except Exception as e:
                            pass
            else:
                if trie.find(ip) < 24:
                    ip_tmp = f"{ip}/{cidr}"
                    try:
                        sql = "insert into target(ip, type, data_center, label) values (%s, %s, %s, %s)"
                        cur.execute(sql, (ip_tmp, 'prefix', item[1], False))
                        count += 1
                    except Exception as e:
                        pass
        else:
            ip = item[0]
            if trie.find(ip) < 24:
                try:
                    sql = "insert into target(ip, type, data_center, label) values (%s, %s, %s, %s)"
                    cur.execute(sql, (ip, 'ip', item[1], False))
                    count += 1
                except Exception as e:
                    pass
        pbar.set_description(f"Current number is {count}")
        pbar.update()

    pbar.close()
    conn.commit()
    cur.close()
    conn.close()

def get_google_public_from_database():
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='usejydjq0078', port=3306, db='gcp')
    cur = conn.cursor()
    sql = f"select ip from target where label = %s"
    cur.execute(sql, (True,))
    data = cur.fetchall()
    database_ip = []
    for i in range(len(data)):
        database_ip.append(data[i][0])

    return database_ip

def tire_create(database_ip):
    trie = Trie()
    for ip_range in database_ip:
        tmp = ip_range.split('/')
        ip = tmp[0]
        cidr = int(tmp[1])
        trie.insert(ip, cidr)
    return trie



if __name__ == "__main__":
    database_ip = None
    trie = None
    try:
        database_ip = get_google_public_from_database()
    except:
        print("database exception")
    if database_ip is not None:
        trie = tire_create(database_ip)


    bgphe_crawl(trie)