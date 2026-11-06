package kcompat;

import android.app.Activity;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

/** 核对没过时的说明页。 */
public final class N extends Activity {
    @Override
    protected void onCreate(Bundle b) {
        // 不用 Readest 的启动主题（黑底加启动图），白底黑字
        setTheme(android.R.style.Theme_Material_Light_NoActionBar);
        super.onCreate(b);
        getWindow().setBackgroundDrawable(new android.graphics.drawable.ColorDrawable(0xffffffff));
        int pad = (int) (24 * getResources().getDisplayMetrics().density);
        LinearLayout l = new LinearLayout(this);
        l.setOrientation(LinearLayout.VERTICAL);
        l.setGravity(Gravity.CENTER);
        l.setPadding(pad, pad, pad, pad);
        l.setBackgroundColor(0xffffffff);
        TextView t = new TextView(this);
        t.setText("本版本是 Readest 的墨卓适配版，\n仅限在墨卓（Kindle 上的安卓）中使用。\n\n在手机上请安装 Readest 官方版。");
        t.setTextSize(18);
        t.setGravity(Gravity.CENTER);
        t.setTextColor(0xff000000);
        l.addView(t);
        Button q = new Button(this);
        q.setText("退出");
        q.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { finish(); }
        });
        l.addView(q);
        setContentView(l);
    }
}
