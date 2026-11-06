#!/usr/bin/env python3
# 把 Tauri 插件命令的方法体换掉（保留 @Command 注解）：用到安卓 8 接口、7.x 上没法做的命令
#   震动插件 4 个命令 → 直接回成功（墨水屏设备没有震动马达）
#   capture_webview_region（PixelCopy，仿真翻页截图）→ 回失败，网页端照它的注释退回渲染器自己的翻页
import re, os
S = os.path.expanduser('~/readest-patch/smali2/')
OK = '    invoke-virtual {p1}, Lapp/tauri/plugin/Invoke;->c()V\n\n    return-void\n'
FAIL = ('    const-string v0, "not supported on Android 7"\n\n    const-string v1, "unsupported"\n\n'
        '    invoke-virtual {p1, v0, v1}, Lapp/tauri/plugin/Invoke;->b(Ljava/lang/String;Ljava/lang/String;)V\n\n    return-void\n')
todo = {
    'app/tauri/haptics/HapticsPlugin.smali': [(n, OK) for n in ('impactFeedback', 'notificationFeedback', 'selectionFeedback', 'vibrate')],
    'com/readest/native_bridge/NativeBridgePlugin.smali': [('capture_webview_region', FAIL)],
}
for f, items in todo.items():
    s = open(S + f).read()
    for name, body in items:
        pat = re.compile(r'(\.method public final %s\(Lapp/tauri/plugin/Invoke;\)V\n)\s*\.registers \d+\n(.*?\.end annotation\n).*?(\.end method)' % name, re.S)
        s, k = pat.subn(lambda m: m.group(1) + '    .registers 4\n' + m.group(2) + '\n' + body + m.group(3), s)
        assert k == 1, (f, name, k)
    open(S + f, 'w').write(s)
