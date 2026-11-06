#!/bin/bash
# Arch：对齐、用墨卓 releasekey（Windows 上的备份）签名、核对
set -e
D=/mnt/d/Documents/Esverde/kindle-android/local/readest
BT=~/kwa/sdk/android/android-11
K=/mnt/c/Users/esverde/.ssh/kindle-android-keys/releasekey
V=$($BT/aapt dump badging $D/unsigned.apk | sed -n "s/.*versionName=.\([0-9.]*\).*/\1/p")
O="$D/Readest_${V}_armv7_android7.apk"
T=$(mktemp -d)
$BT/zipalign -f -p 4 $D/unsigned.apk $T/aligned.apk
$BT/apksigner sign --key $K.pk8 --cert $K.x509.pem --min-sdk-version 24 --out $T/signed.apk $T/aligned.apk
$BT/apksigner verify -v --min-sdk-version 24 --print-certs $T/signed.apk | grep -E "Verified using|Signer #1 certificate SHA-256"
$BT/zipalign -c -p 4 $T/signed.apk && echo aligned
cp $T/signed.apk "$O"; rm -rf $T $D/unsigned.apk
$BT/aapt dump badging "$O" | grep -E "^(package|sdkVersion|native-code)"
sha256sum "$O"
