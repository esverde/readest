# Readest 0.12.20 墨卓适配版（安卓 7）

**非官方修改版**，问题请勿反馈给 Readest 原作者。

[墨卓](https://github.com/esverde/kindle-android)是跑在越狱 Kindle 上的安卓 7.1（armv7）。官方 Readest 最低要安卓 8（minSdk 26），
这里不改 Readest 源码、不重新编译，而是对**官方发布的** `Readest_0.12.20_armv7.apk` 打补丁，产出
`Readest_0.12.20_armv7_android7.apk`：

- 最低版本改成安卓 7.0（minSdk 24），版本号不变（0.12.20 / 12020），包名不变（`com.bilingify.readest`）。
- 补上安卓 7 缺的几处调用（`String.join`、`Long.compareUnsigned`、`Method.getParameterCount`、
  `WebView.getCurrentWebViewPackage`、`Configuration.colorMode`、触感反馈等，见 `readest-build.sh`、`readest-haptics.py`、`kcompat.smali`）。
- 启动图标：安卓 7 不认 adaptive-icon，资源表里 `res/BW.xml` 改指 `res/BW.png`（`BW.png`）。
- **只在墨卓上运行**：`kcompat/G.java` 在 `MainActivity.onCreate` 开头核对系统包 `android` 的签名证书
  是不是墨卓的 platform 证书（不挑墨卓版本、机型），不是就打开说明页 `kcompat/N.java` 并结束进程。
  这是程序功能，不是许可条款；按 AGPL-3.0，你可以删掉它自己重新打包。
- 用墨卓的密钥重新签名（所以不能覆盖安装官方版，要先卸载）。

已知问题：朗读没修（会崩）。在 Kindle 上冷启动白屏约 15 秒，是 WebView 执行 Readest 网页界面的 JavaScript，0.12.16 也一样。

## 文件

| 文件 | 作用 |
|---|---|
| `readest-smali.sh` | baksmali 官方 `classes.dex`，列出安卓 7 上缺的调用 |
| `readest-build.sh` | 主流程：sed 替换、换方法体、并入兼容类和墨卓限制、smali 回 dex、改包、签名 |
| `readest-haptics.py` | 换掉用到安卓 8 接口的触感反馈命令方法体 |
| `kcompat.smali` | 兼容类 `kcompat.C`（`compareUnsigned`、`getParameterCount` 的替代） |
| `kcompat/G.java`、`kcompat/N.java` | 墨卓限制（核对签名 / 说明页） |
| `readest-gate.sh` | 把 `kcompat/*.java` 编成 `gate.dex`（javac `--release 8` + d8 `--min-api 24`） |
| `readest-patch.py` | 改二进制 `AndroidManifest.xml`（minSdk 26→24、加说明页 activity）和 `resources.arsc`，换 `classes.dex` |
| `readest-sign.sh` | zipalign、apksigner 签名（v2/v3，min-sdk 24） |
| `api-check.py` 等 | 审查：应用 dex 引用了哪些安卓 7.1 启动类路径里没有的类 / 方法 / 字段，按引入版本归类 |

## 复现

脚本原样保留了编出发布包时的路径，换环境时改开头的变量：

- `T`：本目录（脚本、`kcompat.smali`、`BW.png`）；`readest-build.sh` 读 `$T/readest-gate/gate.dex`，即 `readest-gate.sh` 的输出。
- `D`：输出目录。`~/readest-patch/`：工作目录，放官方包 `orig.apk` 和从里面解出的 `classes.dex`。
- `~/kwa/sdk/smali/{baksmali,smali}.jar`（smali 2.x）、`~/kwa/sdk/android/android-11/`（zipalign、apksigner、aapt）。
- `readest-sign.sh` 的 `K`：签名密钥（墨卓的 releasekey，不公开；自己打包换成自己的密钥）。
- `api-check.py` 要安卓 7.1 的启动类路径 dex（`sys71fw/*.dex`，从墨卓系统的 `/system/framework/` 取），
  `readest-apilevel.py` 要 Android SDK 的 `api-versions.xml`。只用于审查，不影响出包。

```sh
mkdir -p ~/readest-patch && cd ~/readest-patch
cp Readest_0.12.20_armv7.apk orig.apk && unzip -o orig.apk classes.dex   # 官方 release 的 armv7 包
bash readest-smali.sh            # 反编译
bash readest-gate.sh             # 编墨卓限制的两个类
bash readest-build.sh            # 打补丁、出包、签名
```

## 许可

Readest（https://github.com/readest/readest）以 [AGPL-3.0](../LICENSE) 发布，版权归 Readest 的作者和贡献者。本目录的补丁脚本和代码同样以 AGPL-3.0 发布。
修改：esverde，2026-10-30（0.12.16）、2026-11-06（0.12.20，加墨卓限制）。
