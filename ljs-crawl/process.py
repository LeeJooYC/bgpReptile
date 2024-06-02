import json
with open('google_rule.json', 'r') as f:
    data = json.load(f)

rule_class = {}
for k, v in data.items():
    for i in v:
        # 将i转换成正则格式，如.进行转义，以*开头的字符串转换成.*，以*结尾的字符串转换成.*$
        i = i.replace('.', '\\.')
        if i.startswith('*.'):
            i = i[2:]
        i = i.replace('*', '.*')
        if i in rule_class:
            rule_class[i].append(str(k))
        else:
            rule_class[i] = [str(k)]

with open('google_rule_processed.json', 'w') as f:
    json.dump(rule_class, f, ensure_ascii=False, indent=4)