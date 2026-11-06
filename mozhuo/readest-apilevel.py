#!/usr/bin/env python3
# api-missing24.txt 里每一项按 api-versions.xml 标出引入版本；API 26 的（R8 按 minSdk 26 删掉了判断）列出在哪些类里用到
import os, re, collections, xml.etree.ElementTree as ET
W = os.path.expanduser('~/readest-patch')
cls_since, mem_since = {}, {}
for c in ET.parse(f'{W}/api-versions.xml').getroot().iter('class'):
    cn = 'L' + c.get('name') + ';'; cs = int(c.get('since', 1)); cls_since[cn] = cs
    for m in c:
        if m.tag in ('method', 'field'):
            mem_since[cn + '->' + m.get('name')] = int(m.get('since', cs))
def since(item):
    if '->' in item:
        c, n = item.split('->', 1)
        if n in ('', None): return None
        k = c + '->' + n
        if k in mem_since: return mem_since[k]
        # 构造方法 / 字段名在 xml 里的写法：方法是 name(args)ret；字段只有名字
        k2 = c + '->' + n.split(':')[0]
        return mem_since.get(k2, cls_since.get(c))
    return cls_since.get(item)
items = []
for l in open(f'{W}/api-missing24.txt'):
    if not l.startswith('  L'): continue
    it = l.strip()
    if ':' in it and '->' not in it:   # 字段写成 Lc;.name:type
        c, rest = it.split(';.', 1); it = c + ';->' + rest.split(':')[0]
    items.append(it)
lv = collections.defaultdict(list)
for it in items: lv[since(it) or 99].append(it)
for k in sorted(lv): print(f'API {k if k != 99 else ">30/未知"}: {len(lv[k])}')
# API 26 的在哪些 smali 文件里出现
print('\n##### API 26 items and where used')
files = {}
for root, _, fs in os.walk(f'{W}/smali2'):
    for f in fs:
        p = os.path.join(root, f); files[p[len(W) + 8:]] = open(p, errors='replace').read()
for it in sorted(lv[26]):
    needle = it if '->' in it else it
    if '->' in it and '(' not in it:   # 字段
        needle = it + ':'
    where = [f for f, t in files.items() if needle in t]
    print(f'{it}\n    used in: {", ".join(sorted(where)[:8])}{" ..." if len(where) > 8 else ""}')
