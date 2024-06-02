import json
from tqdm import tqdm
from shodan import Shodan
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
        return 0

def decimalism2ip(dec_value):
    ip = ''
    t = 2 ** 8
    for _ in range(4):
        v = dec_value % t
        ip = '.' + str(v) + ip
        dec_value = dec_value // t
    ip = ip[1:]
    return ip


'''''''''
papers = []  # 该数组每行都是字典数据{}

read_file = open("mysql.json", 'r', encoding='utf-8')
write_file_1 = open("mysql-cloud.json", 'w', encoding='utf-8')
write_file_2 = open("mysql-nocloud.json", 'w', encoding='utf-8')

for line in tqdm(read_file.readlines()):
    dic = json.loads(line)
    if 'tags' in dic and dic['tags'][0] == 'cloud':
        write_file_1.write(line)
    else:
        write_file_2.write(line)

read_file.close()
write_file_1.close()
write_file_2.close()
'''''''''


def update_from_shodan(api, page_number, trie, search_item):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='usejydjq0078', port=3306, db='gcp')
    count = 0

    pbar = tqdm(total=page_number)
    pbar.set_description(f"Current number is {count}")

    for i in range(1, page_number):
        cur = conn.cursor()

        results = api.search(search_item, page=i)
        for result in results['matches']:
            if 'cloud' in str(result):
                if 'ip_str' in result:
                    if '/' in result['ip_str']:
                        tmp = result['ip_str'].split('/')
                        ip = tmp[0]
                        cidr = int(tmp[1])
                        ip_int = ipv42int(ip)
                        if cidr < 24:
                            for i in range(2**(24-cidr)):
                                ip_tmp = ip_int + i*256
                                ip_tmp = str(ipaddress.ip_address(ip_tmp))
                                if trie.find(ip_tmp) == 0:
                                    ip_tmp = f"{ip_tmp}/24"
                                    sql = "insert into target(ip, type, data_center, label) values (%s, %s, %s, %s)"
                                    cur.execute(sql, (ip_tmp, 'prefix', None, False))
                                    count += 1
                        else:
                            if trie.find(ip) == 0:
                                ip_tmp = f"{ip}/{cidr}"
                                sql = "insert into target(ip, type, data_center, label) values (%s, %s, %s, %s)"
                                cur.execute(sql, (ip_tmp, 'prefix', None, False))
                                count += 1
                    else:
                        ip = result['ip_str']
                        if trie.find(ip) == 0:
                            sql = "insert into target(ip, type, data_center, label) values (%s, %s, %s, %s)"
                            cur.execute(sql, (ip, 'ip', None, False))
                            count += 1
        # print(count)
        pbar.set_description(f"Current number is {count}")
        pbar.update()
        conn.commit()
        cur.close()
    conn.close()
    pbar.close()

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

    SHODAN_API_KEY = "TYI8icr6oAIS6VrCi6jKSfGINxLHNAGd"
    api = Shodan(SHODAN_API_KEY)

    page_number = 10
    update_from_shodan(api, page_number, trie, 'country:"us" org:"google" state:"MO"')
