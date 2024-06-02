1. 项目基于python3.9，依赖在requirements.txt中
2. 起始种子域名保存在google_seed_domains.json中
3. 域名规则保存在google_rule.json中，首先运行process.py处理规则，生成google_rule_processed.json
4. 目前默认规则有3类，id为0，1，2，若有修改请修改aliyun_main.py中class_ids中的值
5. 运行aliyun_main.py，将生成3个文件：
    result_ip_class.json：每个类型规则命中的IP；
    result_ip.json：所有规则命中的IP；
    result_ip_class.json：每个类型规则命中的域名和IP