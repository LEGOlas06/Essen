package io.github.legolas06.tellerflamme;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.widget.RemoteViews;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.Locale;

/** Homescreen-Widget: Streak, Maskottchen, Motivationsspruch und Kalorien von heute. */
public class StreakWidget extends AppWidgetProvider {
    static final String PREFS = "tellerflamme_widget";

    @Override
    public void onUpdate(Context c, AppWidgetManager m, int[] ids) {
        for (int id : ids) m.updateAppWidget(id, build(c));
    }

    public static void updateAll(Context c) {
        AppWidgetManager m = AppWidgetManager.getInstance(c);
        int[] ids = m.getAppWidgetIds(new ComponentName(c, StreakWidget.class));
        for (int id : ids) m.updateAppWidget(id, build(c));
    }

    private static long daysBetween(String a, String b) {
        try {
            SimpleDateFormat f = new SimpleDateFormat("yyyy-MM-dd", Locale.GERMANY);
            Date da = f.parse(a), db = f.parse(b);
            return Math.round((db.getTime() - da.getTime()) / 86400000.0);
        } catch (ParseException | NullPointerException e) {
            return 9999;
        }
    }

    static RemoteViews build(Context c) {
        SharedPreferences p = c.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        int streak = p.getInt("streak", 0);
        int freezes = p.getInt("freezes", 0);
        String last = p.getString("lastDate", "");
        String today = new SimpleDateFormat("yyyy-MM-dd", Locale.GERMANY).format(new Date());
        int kcal = today.equals(p.getString("today", "")) ? p.getInt("kcal", 0) : 0;
        int goal = Math.max(1, p.getInt("goal", 2000));
        int hour = Calendar.getInstance().get(Calendar.HOUR_OF_DAY);
        long gap = last.isEmpty() ? 9999 : daysBetween(last, today);

        boolean done = gap == 0;
        String msg;
        int face;
        if (done) {
            face = R.drawable.mascot_happy;
            if (kcal >= goal * 0.9 && kcal <= goal * 1.1) msg = "Ziel getroffen. Legendär!";
            else if (hour >= 17) msg = "Heute erledigt. Abendessen nicht vergessen!";
            else msg = "Heute erledigt. Weiter so!";
        } else if (streak > 0 && gap == 1) {
            face = R.drawable.mascot_sad;
            if (hour >= 20) msg = "Letzte Chance! Rette deinen Streak!";
            else if (hour >= 15) msg = "Ich hab Hunger auf Einträge…";
            else msg = "Was gab's zum Frühstück?";
        } else if (streak > 0 && gap - 1 <= freezes) {
            face = R.drawable.mascot_sad;
            msg = "Ein Freeze hat dich gerettet. Jetzt eintragen!";
        } else {
            face = R.drawable.mascot_sad;
            streak = 0;
            msg = "Starte heute einen neuen Streak!";
        }

        RemoteViews v = new RemoteViews(c.getPackageName(), R.layout.widget_streak);
        v.setTextViewText(R.id.w_streak, String.valueOf(streak));
        v.setImageViewResource(R.id.w_flame, done ? R.drawable.flame_on : R.drawable.flame_off);
        v.setImageViewResource(R.id.w_mascot, face);
        v.setTextViewText(R.id.w_msg, msg);
        v.setTextViewText(R.id.w_kcal, kcal + " / " + goal + " kcal");
        v.setProgressBar(R.id.w_bar, goal, Math.min(kcal, goal), false);

        Intent open = new Intent(c, MainActivity.class);
        open.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent pi = PendingIntent.getActivity(c, 0, open, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        v.setOnClickPendingIntent(R.id.w_root, pi);
        return v;
    }
}
