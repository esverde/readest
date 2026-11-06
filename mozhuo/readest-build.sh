#!/bin/bash
# 官方 Readest armv7（0.12.16 起，换版本时 orig.apk 换成新包） → 安卓 7.0 可装可跑的包（墨卓签名）。先跑 readest-smali.sh 反编译出 ~/readest-patch/smali
set -e
T=/mnt/d/Documents/Esverde/kindle-android/local/tmp
D=/mnt/d/Documents/Esverde/kindle-android/local/readest
cd ~/readest-patch
rm -rf smali2 && cp -r smali smali2 && mkdir -p smali2/kcompat && cp $T/kcompat.smali smali2/kcompat/C.smali
F=$(grep -rlE --include=*.smali 'BootstrapMethodError|String;->join\(|compareUnsigned|getParameterCount\(\)I|reflect/Executable;' smali2)
sed -i -E \
  -e 's#Ljava/lang/BootstrapMethodError;#Ljava/lang/VerifyError;#g' \
  -e 's#Ljava/lang/String;->join\(Ljava/lang/CharSequence;Ljava/lang/Iterable;\)#Landroid/text/TextUtils;->join(Ljava/lang/CharSequence;Ljava/lang/Iterable;)#g' \
  -e 's#Ljava/lang/Long;->compareUnsigned\(JJ\)I#Lkcompat/C;->cu(JJ)I#g' \
  -e 's#invoke-virtual(/range)? \{([^}]*)\}, Ljava/lang/reflect/(Method|Constructor);->getParameterCount\(\)I#invoke-static\1 {\2}, Lkcompat/C;->pc(Ljava/lang/reflect/\3;)I#g' \
  -e 's#Ljava/lang/reflect/Executable;#Ljava/lang/reflect/AccessibleObject;#g' \
  $F
# WebView.getCurrentWebViewPackage 是安卓 8 的；7.x 用 WebViewFactory.getLoadedPackageInfo（同样返回当前 WebView 的包信息）
sed -i 's#Landroid/webkit/WebView;->getCurrentWebViewPackage()#Landroid/webkit/WebViewFactory;->getLoadedPackageInfo()#g' \
  $(grep -rl --include=*.smali 'getCurrentWebViewPackage' smali2)
python3 $T/readest-haptics.py
# 墨卓限制：kcompat.G（核对系统签名）/ kcompat.N（说明页），源码 readest-gate/，KPW6-AOSP 上 readest-gate.sh 编成 gate.dex
java -jar ~/kwa/sdk/smali/baksmali.jar d $T/readest-gate/gate.dex -o smali2
M=smali2/com/bilingify/readest/MainActivity.smali
grep -q '^    .registers 12$' <(sed -n '/^.method public final onCreate(Landroid\/os\/Bundle;)V/,+1p' $M)
sed -i '/^.method public final onCreate(Landroid\/os\/Bundle;)V/{n;s#$#\n\n    invoke-static {p0}, Lkcompat/G;->check(Landroid/app/Activity;)V#}' $M
# AppCompatActivity.attachBaseContext 算配置差异时读写 Configuration.colorMode（安卓 8 的字段）：7.x 没有，读出当 0、不写回
A=smali2/i/h.smali
[ $(grep -c 'Landroid/content/res/Configuration;->colorMode:I' $A) -gt 0 ]   # 0.12.16 是 4 处、0.12.20 是 8 处
sed -i -E -e 's#^(\s*)iget (v[0-9]+), v[0-9]+, Landroid/content/res/Configuration;->colorMode:I#\1const/4 \2, 0x0#' \
          -e 's#^(\s*)iput v[0-9]+, v[0-9]+, Landroid/content/res/Configuration;->colorMode:I#\1nop#' $A
# jackson 的 Java 7 扩展（java.nio.file.Path 的序列化）：原来反射探测、没有就留 null；按安卓 8 编译时探测被优化掉了。一律当没有
J=smali2/com/fasterxml/jackson/databind/ext/d.smali
grep -q 'sput-object v0, Lcom/fasterxml/jackson/databind/ext/d;->q:' $J
sed -i 's#^    sput-object v0, Lcom/fasterxml/jackson/databind/ext/d;->q:#    const/4 v0, 0x0\n\n&#' $J
echo "left: $(grep -rcE --include=*.smali 'BootstrapMethodError|String;->join\(|Long;->compareUnsigned|reflect/(Method|Constructor);->getParameterCount|reflect/Executable;' smali2 | grep -v ':0' | wc -l)"
java -jar ~/kwa/sdk/smali/smali.jar a -a 24 smali2 -o classes24.dex
head -c 8 classes24.dex | od -c | head -1
python3 $T/readest-patch.py orig.apk classes24.dex $D/BW.png $D/unsigned.apk
bash $T/readest-sign.sh
