#!/usr/bin/env python3
# 应用 dex 引用的系统类 / 方法 / 字段，在安卓 7.1 的启动类路径（sys71fw/*.dex）里解析不到的列出来。
# 用法：api-check.py <app.dex> [更多 app dex]
import sys, struct, glob, os, collections

def uleb(b, p):
    r = s = 0
    while True:
        x = b[p]; p += 1; r |= (x & 0x7f) << s; s += 7
        if x < 0x80: return r, p

class Dex:
    def __init__(self, path):
        b = self.b = open(path, 'rb').read()
        g = lambda o: struct.unpack_from('<II', b, o)
        (ns, os_), (nt, ot), (np_, op), (nf, of), (nm, om), (nc, oc) = g(56), g(64), g(72), g(80), g(88), g(96)
        def s(i):
            o = struct.unpack_from('<I', b, os_ + i * 4)[0]
            _, o = uleb(b, o); e = b.index(0, o); return b[o:e].decode('utf8', 'replace')
        self.str = [s(i) for i in range(ns)]
        self.typ = [self.str[struct.unpack_from('<I', b, ot + i * 4)[0]] for i in range(nt)]
        def proto(i):
            sh, rt, po = struct.unpack_from('<III', b, op + i * 12)
            ps = []
            if po:
                n = struct.unpack_from('<I', b, po)[0]
                ps = [self.typ[x] for x in struct.unpack_from('<%dH' % n, b, po + 4)]
            return '(' + ''.join(ps) + ')' + self.typ[rt]
        self.proto = [proto(i) for i in range(np_)]
        self.fld = [(self.typ[c], self.str[n], self.typ[t]) for c, t, n in (struct.unpack_from('<HHI', b, of + i * 8) for i in range(nf))]
        self.meth = [(self.typ[c], self.str[n], self.proto[p]) for c, p, n in (struct.unpack_from('<HHI', b, om + i * 8) for i in range(nm))]
        self.classes = {}
        for i in range(nc):
            c, _, sup, ifo, _, _, cd, _ = struct.unpack_from('<8I', b, oc + i * 32)
            ifs = []
            if ifo:
                n = struct.unpack_from('<I', b, ifo)[0]
                ifs = [self.typ[x] for x in struct.unpack_from('<%dH' % n, b, ifo + 4)]
            ms, fs = set(), set()
            if cd:
                p = cd; a = []
                for _ in range(4): v, p = uleb(b, p); a.append(v)
                for k, cnt in enumerate(a):
                    idx = 0
                    for _ in range(cnt):
                        d, p = uleb(b, p); idx += d; _, p = uleb(b, p)
                        if k >= 2: _, p = uleb(b, p); ms.add(self.meth[idx][1:])
                        else: fs.add(self.fld[idx][1:])
            self.classes[self.typ[c]] = (self.typ[sup] if sup != 0xffffffff else None, ifs, ms, fs)

boot = {}
for f in sorted(glob.glob(os.path.join(os.path.dirname(__file__), 'sys71fw', '*.dex'))):
    boot.update(Dex(f).classes)
apps = [Dex(p) for p in sys.argv[1:]]
allc = dict(boot)
for a in apps: allc.update(a.classes)

def has(cls, key, kind, seen=None):
    seen = seen or set()
    if cls in seen or cls not in allc: return False
    seen.add(cls)
    sup, ifs, ms, fs = allc[cls]
    if key in (ms if kind == 'm' else fs): return True
    return any(has(x, key, kind, seen) for x in [sup] + ifs if x)

SYS = ('Ljava/', 'Ljavax/', 'Landroid/', 'Ldalvik/', 'Lorg/json/', 'Lorg/w3c/', 'Lorg/xml/', 'Lsun/', 'Llibcore/', 'Lorg/apache/http/')
def sysref(c):
    c = c.lstrip('[')
    return c.startswith(SYS) and not c.startswith(('Landroid/support/', 'Landroidx/'))
miss_c, miss_m, miss_f = set(), collections.Counter(), collections.Counter()
for a in apps:
    for t in a.typ:
        t2 = t.lstrip('[')
        if sysref(t2) and t2 not in boot and t2 not in a.classes: miss_c.add(t2)
    for c, n, p in a.meth:
        if c.lstrip('[').startswith('L') and (sysref(c) or c in a.classes) and c.lstrip('[') not in miss_c:
            if c in a.classes and not any(sysref(x) for x in [a.classes[c][0]] + a.classes[c][1] if x): continue
            if not has(c.lstrip('['), (n, p), 'm') and not c.startswith('['):
                # 应用自己类里定义的不算
                if c in a.classes and (n, p) in a.classes[c][2]: continue
                if sysref(c) or not has(c, (n, p), 'm'): miss_m[f'{c}->{n}{p}'] += 1
    for c, n, t in a.fld:
        if sysref(c) and c not in miss_c and not has(c, (n, t), 'f'): miss_f[f'{c}.{n}:{t}'] += 1
print(f'boot classes: {len(boot)}')
print(f'== missing classes ({len(miss_c)})'); [print(' ', c) for c in sorted(miss_c)]
mm = [m for m in miss_m if m.split('->')[0].startswith(SYS)]
print(f'== missing system methods ({len(mm)})'); [print(' ', m) for m in sorted(mm)]
print(f'== missing system fields ({len(miss_f)})'); [print(' ', f) for f in sorted(miss_f)]
