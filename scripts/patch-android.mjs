// Ergänzt das von Capacitor erzeugte Android-Projekt um Health Connect und Kamera.
import fs from 'node:fs';
const mf = 'android/app/src/main/AndroidManifest.xml';
let x = fs.readFileSync(mf, 'utf8');
const perms = `
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.health.READ_ACTIVE_CALORIES_BURNED" />
    <uses-permission android:name="android.permission.health.READ_WEIGHT" />
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
`;
if (!x.includes('READ_ACTIVE_CALORIES_BURNED')) {
  x = x.replace(/<application/, perms + '\n    <application');
  x = x.replace(/<\/application>/, acts + '    </application>');
  fs.writeFileSync(mf, x);
}
const vg = 'android/variables.gradle';
let v = fs.readFileSync(vg, 'utf8');
v = v.replace(/minSdkVersion\s*=\s*\d+/, 'minSdkVersion = 26');
fs.writeFileSync(vg, v);
console.log('Android-Projekt angepasst');
