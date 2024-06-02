import ipaddress
import json
from tqdm import tqdm
import pymysql


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
        return 0

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

def update_from_ljs(trie):
    fo = open("result_ips.json", "r")
    res = json.load(fo)
    fo.close()

    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='usejydjq0078', port=3306, db='gcp')
    cur = conn.cursor()
    count = 0

    pbar = tqdm(total=len(res))
    pbar.set_description(f"Current number is {count}")
    for item in res:
        if '/' in item:
            tmp = item.split('/')
            ip = tmp[0]
            cidr = int(tmp[1])
            ip_int = ipv42int(ip)
            if cidr < 24:
                for i in range(2 ** (24 - cidr)):
                    ip_tmp = ip_int + i * 256
                    ip_tmp = str(ipaddress.ip_address(ip_tmp))
                    if trie.find(ip_tmp) < 24:
                        ip_tmp = f"{ip_tmp}/24"
                        sql = "insert into target(ip, type, data_center, label) values (%s, %s, %s, %s)"
                        cur.execute(sql, (ip_tmp, 'prefix', None, False))
                        count += 1
            else:
                if trie.find(ip) < 24:
                    ip_tmp = f"{ip}/{cidr}"
                    sql = "insert into target(ip, type, data_center, label) values (%s, %s, %s, %s)"
                    cur.execute(sql, (ip_tmp, 'prefix', None, False))
                    count += 1
        else:
            ip = item
            if trie.find(ip) < 24:
                sql = "insert into target(ip, type, data_center, label) values (%s, %s, %s, %s)"
                cur.execute(sql, (ip, 'ip', None, False))
                count += 1
        pbar.set_description(f"Current number is {count}")
        pbar.update()

    pbar.close()
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    database_ip = None
    trie = None
    try:
        database_ip = get_google_public_from_database()
    except:
        print("database exception")
    if database_ip is not None:
        trie = tire_create(database_ip)

    update_from_ljs(trie)
