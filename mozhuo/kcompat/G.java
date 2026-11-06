package kcompat;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.Signature;
import java.security.MessageDigest;

/** 墨卓限制：系统包 android 的签名证书必须是墨卓 platform 证书（不挑版本、机型）。在 MainActivity.onCreate 开头调用。 */
public final class G {
    static final String PLATFORM_CERT_SHA256 = "968254ddd88548a0f296d2c6e267d30a90f6ecbb8919605db3dba324fdd0527c";

    public static boolean matches(Signature[] sigs) {
        if (sigs == null) return false;
        try {
            for (Signature s : sigs) {
                byte[] d = MessageDigest.getInstance("SHA-256").digest(s.toByteArray());
                StringBuilder b = new StringBuilder();
                for (byte x : d) b.append(String.format("%02x", x));
                if (PLATFORM_CERT_SHA256.equals(b.toString())) return true;
            }
        } catch (Exception e) { }
        return false;
    }

    @SuppressWarnings("deprecation")
    public static void check(Activity a) {
        boolean ok;
        try {
            ok = matches(a.getPackageManager().getPackageInfo("android", PackageManager.GET_SIGNATURES).signatures);
        } catch (Exception e) {
            ok = false;
        }
        if (ok) return;
        // 不是墨卓：开说明页，结束本进程（Tauri 的 WebView、Rust 后端都不起）。说明页在新进程里起来
        a.startActivity(new Intent(a, N.class));
        android.os.Process.killProcess(android.os.Process.myPid());
    }
}
