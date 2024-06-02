import json
import requests
import pymysql
from tqdm import tqdm


def code2city():
    code2city = {}
    with open('code2city', 'r', encoding='utf-8') as read_file:
        for line in read_file.readlines():
            code2city[line.strip().split(',')[0]] = line.strip().split(',')[1]
    return code2city


def get_open_list(code2city):
    url = 'https://www.gstatic.com/ipranges/cloud.json'
    headers = {'Connection': 'close'}
    response = requests.get(url, headers=headers, verify=False)
    if response.status_code != 200:
        raise Exception("not 200")
    prefixes_list = json.loads(response.text)['prefixes']

    #with open("test.json", 'r') as read_file:
    #    prefixes_list = json.load(read_file)['prefixes']

    ip2city = {}
    for prefix in prefixes_list:
        number = 1
        if 'ipv4Prefix' in prefix and ('global' in prefix['scope'] or 'us-' in prefix['scope'] or 'asia-east1' in
                                       prefix['scope']):
            ip = prefix['ipv4Prefix'].split('/')[0].split('.')
            mask_number = int(prefix['ipv4Prefix'].split('/')[1])

            if mask_number < 16 and mask_number >= 8:
                ip_list = []
                for _ in range(16 - mask_number):
                    number = 2 * number
                for j in range(number):
                    ip_list.append(ip[0] + '.' + str(int(ip[1]) + j) + '.' + ip[2] + '.' + ip[3])
                for i in range(len(ip_list)):
                    for k in range(256):
                        new_ip = ip_list[i].split('.')
                        network_address = new_ip[0] + '.' + new_ip[1] + '.' + str(int(new_ip[2]) + k) + '.' + \
                                          new_ip[3] + '/24'
                        try:
                            ip2city[network_address] = code2city[prefix['scope']]
                        except KeyError:
                            ip2city[network_address] = prefix['scope']

            elif mask_number < 24 and mask_number >= 16:
                for _ in range(24 - mask_number):
                    number = 2 * number
                for j in range(number):
                    network_address = ip[0] + '.' + ip[1] + '.' + str(int(ip[2]) + j) + '.' + ip[3] + '/24'
                    try:
                        ip2city[network_address] = code2city[prefix['scope']]
                    except KeyError:
                        ip2city[network_address] = prefix['scope']
    return ip2city


def database_update(ip2city):
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='usejydjq0078', port=3306, db='gcp')
    cur = conn.cursor()
    sql = f"select ip from target where label = %s"
    cur.execute(sql, (True,))
    data = cur.fetchall()
    database_ip = []
    for i in range(len(data)):
        database_ip.append(data[i][0])

    for i in tqdm(range(len(database_ip))):
        if database_ip[i] not in ip2city:
            sql = "delete from target where target.ip = %s"
            cur.execute(sql, (database_ip[i],))
        else:
            sql = "update target set type = %s, data_center = %s, label = %s where target.ip = %s"
            cur.execute(sql, ('prefix', ip2city[database_ip[i]], True, database_ip[i]))

    for ip in ip2city:
        if ip not in database_ip:
            sql = "insert into target(ip, type, data_center, label) values (%s, %s, %s, %s)"
            #print(sql)
            cur.execute(sql, (ip, 'prefix', ip2city[ip], True))

    conn.commit()
    cur.close()
    conn.close()
    return



if __name__ == "__main__":
    while True:
        try:
            ip2city = get_open_list(code2city())
            # print(ip2city)
            database_update(ip2city)
        except Exception as e:
            print(e)
        break
