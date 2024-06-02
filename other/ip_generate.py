import socket
from tqdm import tqdm
import requests
import re


def is_valid_ip(ip):
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False


def get_unique_ip():
    ip_set = set()
    ip_list = []
    with open("B-cloud-ip", 'r') as read_file:
        for line in tqdm(read_file):
            ip_set.add(line.strip().split('/')[0])
    for ip in ip_set:
        if is_valid_ip(ip):
            ip_list.append(ip)
    ip_list.sort(key=socket.inet_aton)
    with open("result", "w") as write_file:
        for ip in ip_list:
            write_file.write(ip + '/24\n')
    return


def ip2cidr():
    ip_list = []
    new_list = []
    with open("result", "r") as read_file:
        for line in read_file:
            ip_list.append(line.strip())
        for i in range(1, len(ip_list)):
            if ip_list[i-1].split('.')[0:3] != ip_list[i].split('.')[0:3]:
                number = ip_list[i-1].split('.')[0:3]
                new_list.append(number[0] + '.' + number[1] + '.' + number[2] + '.0/24\n')
    with open("cidr", "w") as write_file:
        for cidr in new_list:
            write_file.write(cidr)
    return


def crawl():
    asn_list = ["396982", "395973", "394639", "394507", "36987", "36492", "36385", "36384", "36040", "36039", "26910",
                "26684", "22859", "22577", "19527", "19448", "19425", "16591", "16550", "15169", "13949", "139190", "139070"]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'}
    cidr_list = []
    for k in tqdm(range(len(asn_list))):
        response = requests.get("https://bgp.tools/as/" + asn_list[k] + "#prefixes", headers=headers)
        page_content = response.text

        country_pattern = re.compile('<img class="flag-img" title="(.*)" src="')
        country_matches = country_pattern.findall(page_content)
        ip_pattern = re.compile('id="pfx-(.*)">')
        ip_matches = ip_pattern.findall(page_content)
        try:
            ip_matches.pop()
        except Exception as e:
            pass
        assert len(country_matches) == len(ip_matches)

        for i in range(len(ip_matches)):
            number = 1
            if is_valid_ip(ip_matches[i].split('/')[0]) != True or 'US' not in country_matches[i]:
                continue
            ip = ip_matches[i].split('/')[0].split('.')
            prefix = int(ip_matches[i].split('/')[1])
            if prefix == 24:
                cidr_list.append(ip_matches[i] + '\n')
            if prefix < 24 and prefix >= 16:
                for _ in range(24 - int(prefix)):
                    number = 2 * number
                for j in range(number):
                    cidr_list.append(ip[0] + '.' + ip[1] + '.' + str(int(ip[2]) + j) + '.' + ip[3] + '/24' + '\n')
            if prefix < 16 and prefix >= 8:
                for _ in range(16 - int(prefix)):
                    number = 2 * number
                for j in range(number):
                    cidr_list.append(ip[0] + '.' + str(int(ip[1]) + j) + '.' + ip[2] + '.' + ip[3] + '/16' + '\n')
        # break
    with open("new_cidr", "a") as write_file:
        for cidr in cidr_list:
            write_file.write(cidr)
    return


def prefix_conversion():
    cidr_list = []
    with open("cidr", 'r') as read_file:
        for line in tqdm(read_file):
            number = 1
            ip = line.strip().split('/')[0].split('.')
            prefix = int(line.strip().split('/')[1])
            if prefix == 24:
                cidr_list.append(line)
            if prefix < 24 and prefix >= 16:
                for _ in range(24 - int(prefix)):
                    number = 2 * number
                for j in range(number):
                    cidr_list.append(ip[0] + '.' + ip[1] + '.' + str(int(ip[2]) + j) + '.' + ip[3] + '/24' + '\n')
            if prefix < 16 and prefix >= 8:
                for _ in range(16 - int(prefix)):
                    number = 2 * number
                for j in range(number):
                    cidr_list.append(ip[0] + '.' + str(int(ip[1]) + j) + '.' + ip[2] + '.' + ip[3] + '/16' + '\n')
    with open("new_cidr", "w") as write_file:
        for cidr in cidr_list:
            write_file.write(cidr)
    return


# get_unique_ip()
# ip2cidr()
# crawl()
prefix_conversion()
