.class public final Lkcompat/C;
.super Ljava/lang/Object;
.source "kcompat"

# 安卓 7.1 没有的 API 26 方法，替官方 Readest 包补上（readest-build.sh 把调用改到这里）

.method public static cu(JJ)I
    .registers 6
    const-wide/high16 v0, -0x8000000000000000L
    xor-long/2addr p0, v0
    xor-long/2addr p2, v0
    cmp-long v0, p0, p2
    return v0
.end method

.method public static pc(Ljava/lang/reflect/Method;)I
    .registers 2
    invoke-virtual {p0}, Ljava/lang/reflect/Method;->getParameterTypes()[Ljava/lang/Class;
    move-result-object v0
    array-length v0, v0
    return v0
.end method

.method public static pc(Ljava/lang/reflect/Constructor;)I
    .registers 2
    invoke-virtual {p0}, Ljava/lang/reflect/Constructor;->getParameterTypes()[Ljava/lang/Class;
    move-result-object v0
    array-length v0, v0
    return v0
.end method
