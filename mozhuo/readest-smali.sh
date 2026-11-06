#!/bin/bash
# 反编译官方 dex，找出安卓 7.1 上缺的几处调用
cd ~/readest-patch
[ -d smali ] || java -jar ~/kwa/sdk/smali/baksmali.jar d -a 26 classes.dex -o smali
for p in 'Ljava/lang/BootstrapMethodError;' 'Ljava/lang/String;->join' 'Ljava/lang/Long;->compareUnsigned' '->getParameterCount()I' 'Ljava/lang/reflect/Executable;' 'Ljava/lang/Thread;->threadId'; do
    echo "=== $p"; grep -rn --include=*.smali -F -- "$p" smali | head -8
done
