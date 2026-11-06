#!/usr/bin/env python3
# smali2 里调用安卓 7.1 缺的方法 / 用缺的类（api-missing.txt）的地方：所在方法里没有 SDK_INT 判断的列为“没保护”。
# R8 把高版本调用外提成只有一条 invoke 的小桥接方法时，判断在调用桥接方法的地方——这种单列，查调用方。
import os, re, collections
W = os.path.expanduser('~/readest-patch')
miss = [l.strip() for l in open(f'{W}/api-missing.txt') if l.startswith('  L')]
mm = [m for m in miss if '->' in m]
mc = [m for m in miss if '->' not in m and ':' not in m]
pat_m = {m: m for m in mm}
results = collections.defaultdict(list)
bridges = []
for root, _, files in os.walk(f'{W}/smali2'):
    for f in files:
        p = os.path.join(root, f); rel = p[len(W) + 8:]
        txt = open(p, errors='replace').read()
        if not any(m in txt for m in mm) and not any(c in txt for c in mc): continue
        cls = re.search(r'^\.class.* (L\S+;)', txt, re.M).group(1)
        for meth in re.findall(r'(\.method .*?\.end method)', txt, re.S):
            hit = [m for m in mm if m in meth] + [c for c in mc if re.search(r'(new-instance|const-class|check-cast|instance-of|sget|sput|iget|iput|filled-new-array|new-array)[^\n]*' + re.escape(c), meth)]
            if not hit: continue
            guarded = 'Landroid/os/Build$VERSION;->SDK_INT' in meth
            name = meth.split('\n', 1)[0]
            body = [l.strip() for l in meth.split('\n')[1:-1] if l.strip() and not l.strip().startswith(('.', '#', ':'))]
            if not guarded and len(body) <= 4:
                bridges.append((cls, name, hit[0])); continue
            if not guarded: results[cls].append((name, hit))
# 桥接方法：找调用方是否有判断
callers = collections.defaultdict(list)
if bridges:
    keys = {f"{c}->{n.split()[-1]}": (c, n, h) for c, n, h in bridges}
    for root, _, files in os.walk(f'{W}/smali2'):
        for f in files:
            txt = open(os.path.join(root, f), errors='replace').read()
            if not any(k in txt for k in keys): continue
            cls = re.search(r'^\.class.* (L\S+;)', txt, re.M).group(1)
            for meth in re.findall(r'(\.method .*?\.end method)', txt, re.S):
                for k in keys:
                    if k in meth and 'Landroid/os/Build$VERSION;->SDK_INT' not in meth:
                        callers[k].append(f"{cls}->{meth.split(chr(10),1)[0].split()[-1]}")
LIB = ('Landroidx/', 'Lio/sentry/', 'Lcom/google/', 'Lcom/fasterxml/', 'Lkotlin', 'Lokhttp3/', 'Lokio/', 'Landroid/support/')
print('### unguarded, app / tauri / obfuscated classes first')
for cls in sorted(results, key=lambda c: (c.startswith(LIB), c)):
    for name, hit in results[cls]:
        print(f"{'LIB ' if cls.startswith(LIB) else 'APP '}{cls} {name.split()[-1]}  <- {hit[0]}")
print('### bridges called without a guard')
for k, v in callers.items():
    print(k, '<-', keys[k][2], '| callers:', ', '.join(v[:4]))
