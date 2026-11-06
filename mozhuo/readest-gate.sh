#!/bin/bash
# KPW6-AOSP builder：编 Readest 墨卓限制的两个类（kcompat.G / kcompat.N）成 dex，放 local/tmp/readest-gate/gate.dex
set -e
E=/home/builder/fqapp; G=/mnt/d/Documents/Esverde/kindle-android/local/tmp/readest-gate
T=$(mktemp -d)
$E/jdk/bin/javac -encoding UTF-8 -nowarn --release 8 -cp $E/sdk/platforms/$(ls $E/sdk/platforms | sort -V | tail -1)/android.jar -d $T $G/kcompat/*.java 2>&1 | grep -v "^warning\|^Note\|bootstrap\|^1 warning" || true
$E/jdk/bin/java -cp $E/sdk/build-tools/36.0.0/lib/d8.jar com.android.tools.r8.D8 --release --min-api 24 --output $T $(find $T -name '*.class')
cp $T/classes.dex $G/gate.dex; rm -rf $T; ls -la $G/gate.dex
