#!/usr/bin/env python3
# 全量审查：改过的 smali2 里，用到安卓 7.1 没有的类 / 方法 / 字段（api-missing24.txt）的每个方法，
# 沿调用关系往上找：任一条到达它的路径上没有 SDK_INT 判断，就列为“可能在 7.1 上走到”。
# 近似规则：方法自己读 SDK_INT 算有判断；实例方法所在类（或子类）只在有判断的方法里 new 出来算有判断；
# 调用关系按 名字+签名 匹配（虚方法也算上同名同签名的接口 / 父类调用）；找不到调用方 = 入口（框架回调、反射、JNI）。
import os, re, collections, sys
W = os.path.expanduser('~/readest-patch')
miss = [l.strip() for l in open(f'{W}/api-missing24.txt') if l.startswith('  L')]
mm = [m for m in miss if '->' in m]
mc = [m for m in miss if '->' not in m and ':' not in m]
mf = [m.split(':')[0].replace('.', '->', 1) + ':' for m in miss if ':' in m and '->' not in m]
SDK = 'Landroid/os/Build$VERSION;->SDK_INT'
meths = {}                      # key "Lcls;->name(proto)" -> dict
cls_super, cls_ifs = {}, {}
news = collections.defaultdict(list)       # 类 -> new-instance 它的方法
callers = collections.defaultdict(set)     # "name(proto)" -> 调用方方法 key
callers_exact = collections.defaultdict(set)
# 版本判断的代理：<clinit> 里由 SDK_INT 赋值的静态字段（media3 的 Util.SDK_INT）、直接返回 SDK_INT 的短方法（sentry 的 BuildInfoProvider）
proxies = set()
for root, _, files in os.walk(f'{W}/smali2'):
    for f in files:
        txt = open(os.path.join(root, f), errors='replace').read()
        if SDK not in txt: continue
        cls = re.search(r'^\.class.* (L\S+;)', txt, re.M).group(1)
        for body in re.findall(r'(\.method .*?\.end method)', txt, re.S):
            if SDK not in body: continue
            for fld in re.findall(r'sget \w+, ' + re.escape(SDK) + r'[^\n]*\n(?:\s*\n)*\s*sput \w+, (\S+)', body): proxies.add(fld)
            code = [l.strip() for l in body.split('\n')[1:-1] if l.strip() and not l.strip().startswith(('.', '#', ':'))]
            if len(code) <= 3 and any(l.startswith('return') for l in code):
                proxies.add(f'{cls}->{body.split(chr(10), 1)[0].split()[-1]}')
print(f'# SDK proxies: {len(proxies)}', file=sys.stderr)
def guarded(body): return SDK in body or any(p in body for p in proxies)
inv = re.compile(r'invoke-\w+(?:/range)? \{[^}]*\}, (L[^;]+;|\[[^,]+)->([^\s(]+)(\([^)]*\)\S+)')
for root, _, files in os.walk(f'{W}/smali2'):
    for f in files:
        txt = open(os.path.join(root, f), errors='replace').read()
        cls = re.search(r'^\.class.* (L\S+;)', txt, re.M).group(1)
        m = re.search(r'^\.super (L\S+;)', txt, re.M); cls_super[cls] = m.group(1) if m else None
        cls_ifs[cls] = re.findall(r'^\.implements (L\S+;)', txt, re.M)
        for body in re.findall(r'(\.method .*?\.end method)', txt, re.S):
            head = body.split('\n', 1)[0]; sig = head.split()[-1]
            key = f'{cls}->{sig}'
            hits = [x for x in mm if x in body]
            hits += [c for c in mc if re.search(r'(new-instance|const-class|check-cast|instance-of|filled-new-array|new-array|invoke-\w+(?:/range)? \{[^}]*\}, )[^\n]*' + re.escape(c), body)]
            hits += [x for x in mf if x in body]
            meths[key] = dict(cls=cls, sig=sig, static=' static ' in head, guarded=guarded(body), hits=hits)
            for t, n, p in inv.findall(body):
                callers[n + p].add(key); callers_exact[f'{t}->{n}{p}'].add(key)
            for t in re.findall(r'new-instance \S+, (L\S+;)', body): news[t].append(key)

def subclasses(c):
    return [k for k, s in cls_super.items() if s == c]

memo = {}
def reach(key, depth=0, stack=()):
    """返回一条没判断就能到达 key 的调用路径（列表），找不到返回 None"""
    if key in memo: return memo[key]
    if key in stack or depth > 12: return None
    m = meths.get(key)
    if m is None or m['guarded']: memo[key] = None; return None
    cls, sig = m['cls'], m['sig']
    if not m['static'] and not sig.startswith('<init>') and not sig.startswith('<clinit>'):
        makers = [k for c in [cls] + subclasses(cls) for k in news.get(c, [])]
        if makers and all(meths.get(k, {}).get('guarded') for k in makers):
            memo[key] = None; return None
    if sig.startswith('<clinit>'):
        memo[key] = [key + '  [类初始化]']; return memo[key]
    if m['static'] or sig.startswith('<init>'):
        cs = set(callers_exact.get(f'{cls}->{sig}', set()))
    else:   # 虚方法：调用目标是本类、父类链或实现的接口（含接口的父接口）
        ts, todo = set(), [cls]
        while todo:
            c = todo.pop()
            if c in ts or c is None: continue
            ts.add(c); todo += [cls_super.get(c)] + cls_ifs.get(c, [])
        cs = set().union(*[callers_exact.get(f'{t}->{sig}', set()) for t in ts])
    cs = {c for c in cs if c != key}
    if not cs:
        memo[key] = [key + '  [入口：没有找到调用方]']; return memo[key]
    for c in sorted(cs):
        p = reach(c, depth + 1, stack + (key,))
        if p: memo[key] = [key] + p; return memo[key]
    memo[key] = None; return None

LIB = ('Landroidx/', 'Lio/sentry/', 'Lcom/google/', 'Lcom/fasterxml/', 'Lkotlin', 'Lokhttp3/', 'Lokio/')
APPP = ('Lcom/bilingify/', 'Lapp/tauri/', 'Lcom/readest/', 'Lcom/plugin/', 'Lcom/tauri/', 'Lcom/norman/')
out = collections.defaultdict(list)
for key, m in meths.items():
    if not m['hits']: continue
    p = reach(key)
    if p: out['APP' if m['cls'].startswith(APPP) else ('LIB' if m['cls'].startswith(LIB) else 'OBF')].append((key, m['hits'][0], p))
for g in ('APP', 'OBF', 'LIB'):
    print(f'##### {g}: {len(out[g])}')
    for key, hit, p in sorted(out[g]):
        print(f'* {key}\n    uses {hit}\n    path: ' + ' <- '.join(x.split('->')[0] + '->' + x.split('->')[1].split('(')[0] for x in p[1:6]) + (' ...' if len(p) > 6 else '') + ('  ' + p[-1].split('  ')[-1] if '  [' in p[-1] else ''))
