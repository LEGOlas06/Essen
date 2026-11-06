// Ergänzt das von Capacitor erzeugte Android-Projekt um Health Connect und Kamera.
import fs from 'node:fs';
const mf = 'android/app/src/main/AndroidManifest.xml';
let x = fs.readFileSync(mf, 'utf8');
const perms = `
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.health.READ_ACTIVE_CALORIES_BURNED" />
    <uses-permission android:name="android.permission.health.READ_WEIGHT" />
    <uses-permission android:name="android.permission.health.READ_STEPS" />
    <queries>
        <package android:name="com.google.android.apps.healthdata" />
        <intent>
            <action android:name="androidx.health.ACTION_SHOW_PERMISSIONS_RATIONALE" />
        </intent>
    </queries>
`;
const acts = `
        <activity
            android:name="com.fit_up.health.capacitor.PermissionsRationaleActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="androidx.health.ACTION_SHOW_PERMISSIONS_RATIONALE" />
            </intent-filter>
        </activity>
        <activity-alias
            android:name="ViewPermissionUsageActivity"
            android:exported="true"
            android:targetActivity="com.fit_up.health.capacitor.PermissionsRationaleActivity"
            android:permission="android.permission.START_VIEW_PERMISSION_USAGE">
            <intent-filter>
                <action android:name="android.intent.action.VIEW_PERMISSION_USAGE" />
                <category android:name="android.intent.category.HEALTH_PERMISSIONS" />
            </intent-filter>
        </activity-alias>
        <receiver android:name=".StreakWidget" android:exported="false" android:label="Tellerflamme Streak">
            <intent-filter>
                <action android:name="android.appwidget.action.APPWIDGET_UPDATE" />
            </intent-filter>
            <meta-data android:name="android.appwidget.provider" android:resource="@xml/streak_widget_info" />
        </receiver>
`;
if (!x.includes('READ_ACTIVE_CALORIES_BURNED')) {
  x = x.replace(/<application/, perms + '\n    <application');
  x = x.replace(/<\/application>/, acts + '    </application>');
  fs.writeFileSync(mf, x);
}
// Widget und eigene Java-Dateien (überschreibt MainActivity)
fs.cpSync('android-extra', 'android', { recursive: true });
const vg = 'android/variables.gradle';
let v = fs.readFileSync(vg, 'utf8');
v = v.replace(/minSdkVersion\s*=\s*\d+/, 'minSdkVersion = 26');
fs.writeFileSync(vg, v);
// Texterkennung (Google ML Kit, Modell in der App enthalten, funktioniert offline)
const bg = 'android/app/build.gradle';
let g = fs.readFileSync(bg, 'utf8');
if (!g.includes('com.google.mlkit:text-recognition')) {
  g = g.replace(/dependencies\s*\{/, "dependencies {\n    implementation 'com.google.mlkit:text-recognition:16.0.1'");
  fs.writeFileSync(bg, g);
}
console.log('Android-Projekt angepasst');
