package io.github.legolas06.tellerflamme;

import android.content.Context;
import android.content.SharedPreferences;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

/** Nimmt den Streak-Stand aus der Web-App entgegen und aktualisiert das Homescreen-Widget. */
@CapacitorPlugin(name = "WidgetBridge")
public class WidgetBridgePlugin extends Plugin {
    @PluginMethod
    public void update(PluginCall call) {
        SharedPreferences.Editor e = getContext().getSharedPreferences(StreakWidget.PREFS, Context.MODE_PRIVATE).edit();
        e.putInt("streak", call.getInt("streak", 0));
        e.putInt("freezes", call.getInt("freezes", 0));
        e.putString("lastDate", call.getString("lastDate", ""));
        e.putString("today", call.getString("today", ""));
        e.putInt("kcal", call.getInt("kcal", 0));
        e.putInt("goal", call.getInt("goal", 2000));
        e.apply();
        StreakWidget.updateAll(getContext());
        call.resolve();
    }
}
