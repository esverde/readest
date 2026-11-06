#!/usr/bin/env python3
# 官方 Readest 包降到安卓 7.0：二进制清单里 uses-sdk 的 minSdkVersion 改成 24；classes.dex 换成改过的（readest-build.sh）；
# 清单里加说明页 <activity android:name="kcompat.N"/>（墨卓限制，见 readest-gate/）；
# 启动图标 res/BW.xml（adaptive-icon，7.1 不认）在资源表里改指同长度的 res/BW.png，并放进这张图。
# 用法：readest-patch.py <输入 apk> <新 classes.dex> <BW.png> <输出 apk（未签名）>
import sys, struct, zipfile

MIN_SDK_ATTR = 0x0101020c

def patch_manifest(b):
    b = bytearray(b)
    pos = struct.unpack_from('<H', b, 2)[0]
    strings, resmap, done = [], [], 0
    while pos < len(b):
        typ, hsz, size = struct.unpack_from('<HHI', b, pos)
        if typ == 0x0001:   # 字符串池
            n, _, flags, sstart, _ = struct.unpack_from('<IIIII', b, pos + 8)
            for i in range(n):
                off = pos + sstart + struct.unpack_from('<I', b, pos + hsz + i * 4)[0]
                if flags & 0x100:
                    l = b[off + 1]; off += 2
                    if b[off - 1] & 0x80: off += 1
                    strings.append(bytes(b[off:off + l]).decode('utf8', 'replace'))
                else:
                    l = struct.unpack_from('<H', b, off)[0]
                    strings.append(bytes(b[off + 2:off + 2 + l * 2]).decode('utf-16le'))
        elif typ == 0x0180:   # 资源 id 表
            resmap = list(struct.unpack_from('<%dI' % ((size - hsz) // 4), b, pos + hsz))
        elif typ == 0x0102 and strings[struct.unpack_from('<I', b, pos + 20)[0]] == 'uses-sdk':
            astart, asize, acount = struct.unpack_from('<HHH', b, pos + 24)
            for i in range(acount):
                a = pos + 16 + astart + i * asize
                an = struct.unpack_from('<I', b, a + 4)[0]
                if an < len(resmap) and resmap[an] == MIN_SDK_ATTR:
                    assert b[a + 15] == 0x10 and struct.unpack_from('<I', b, a + 16)[0] == 26
                    struct.pack_into('<I', b, a + 16, 24); done += 1
        pos += size
    assert done == 1, done
    return bytes(b)

NAME_ATTR = 0x01010003
ANDROID_NS = 'http://schemas.android.com/apk/res/android'

def add_activity(b, cls):
    """在 </application> 前插一个 <activity android:name=cls/>（无 intent-filter，默认不导出）。"""
    b = bytearray(b)
    sp = struct.unpack_from('<H', b, 2)[0]
    typ, hsz, size = struct.unpack_from('<HHI', b, sp)
    n, nstyle, flags, sstart, _ = struct.unpack_from('<IIIII', b, sp + 8)
    assert typ == 0x0001 and nstyle == 0
    offs = list(struct.unpack_from('<%dI' % n, b, sp + hsz))
    data = bytes(b[sp + sstart:sp + size])
    utf8 = bool(flags & 0x100)
    def get(i):
        o = sstart + offs[i] + sp
        if utf8:
            o += 2 if b[o] & 0x80 else 1
            l = b[o]; o += 1
            if l & 0x80: l = ((l & 0x7f) << 8) | b[o]; o += 1
            return bytes(b[o:o + l]).decode('utf8')
        l = struct.unpack_from('<H', b, o)[0]
        return bytes(b[o + 2:o + 2 + l * 2]).decode('utf-16le')
    strs = [get(i) for i in range(n)]
    # 资源 id 表在字符串池后面
    rp = sp + size
    rt, rh, rs = struct.unpack_from('<HHI', b, rp); assert rt == 0x0180
    resmap = struct.unpack_from('<%dI' % ((rs - rh) // 4), b, rp + rh)
    i_name = resmap.index(NAME_ATTR)
    assert strs[i_name] == 'name'
    i_act, i_app, i_ns = strs.index('activity'), strs.index('application'), strs.index(ANDROID_NS)
    assert cls not in strs
    if utf8:
        e = cls.encode('utf8'); assert len(e) < 128
        entry = bytes([len(cls), len(e)]) + e + b'\0'
    else:
        entry = struct.pack('<H', len(cls)) + cls.encode('utf-16le') + b'\0\0'
    i_new = n
    data2 = data + entry
    data2 += b'\0' * (-len(data2) % 4)
    pool = struct.pack('<HHIIIIII', 0x0001, hsz, 0, n + 1, 0, flags, hsz + 4 * (n + 1), 0)[:hsz]
    pool += struct.pack('<%dI' % (n + 1), *(offs + [len(data)])) + data2
    pool = pool[:4] + struct.pack('<I', len(pool)) + pool[8:]
    b = b[:sp] + pool + b[sp + size:]
    # 找 </application>
    pos, end_app, line = struct.unpack_from('<H', b, 2)[0], None, 0
    while pos < len(b):
        t, h, sz = struct.unpack_from('<HHI', b, pos)
        if t in (0x0102, 0x0103):
            line = struct.unpack_from('<I', b, pos + 8)[0]
            if t == 0x0103 and struct.unpack_from('<I', b, pos + 20)[0] == i_app: end_app = pos; break
        pos += sz
    assert end_app
    start = struct.pack('<HHIII', 0x0102, 16, 56, line, 0xffffffff) + struct.pack('<IIHHHHHH', 0xffffffff, i_act, 20, 20, 1, 0, 0, 0)
    start += struct.pack('<IIIHBBI', i_ns, i_name, i_new, 8, 0, 0x03, i_new)
    endt = struct.pack('<HHIIIII', 0x0103, 16, 24, line, 0xffffffff, 0xffffffff, i_act)
    b = b[:end_app] + start + endt + b[end_app:]
    struct.pack_into('<I', b, 4, len(b))
    return bytes(b)

def patch_arsc(b):
    assert b.count(b'res/BW.xml') == 1
    return b.replace(b'res/BW.xml', b'res/BW.png')

src, dex, png, dst = sys.argv[1:5]
with zipfile.ZipFile(src) as zi, zipfile.ZipFile(dst, 'w') as zo:
    for it in zi.infolist():
        if it.filename.startswith('META-INF/') and it.filename.rsplit('.', 1)[-1] in ('SF', 'RSA', 'EC', 'DSA', 'MF'):
            continue
        d = zi.read(it)
        if it.filename == 'AndroidManifest.xml': d = add_activity(patch_manifest(d), 'kcompat.N')
        elif it.filename == 'classes.dex': d = open(dex, 'rb').read(); assert d[:8] in (b'dex\n035\x00', b'dex\n037\x00')
        elif it.filename == 'resources.arsc': d = patch_arsc(d)
        zo.writestr(it, d, compress_type=it.compress_type)
    zo.write(png, 'res/BW.png', compress_type=zipfile.ZIP_STORED)
print('ok', dst)
