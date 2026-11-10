# Tellerflamme in Home Assistant

Die Erweiterung `custom_components/tellerflamme` macht Home Assistant zur gemeinsamen Ablage für die Tellerflamme-App:

- **Abgleich zwischen Geräten:** Tagebuch, Vorrat, eigene Lebensmittel, Rezepte, Körperwerte und Ziele. Jeder Eintrag hat eine eigene ID, deshalb gibt es keine doppelten Einträge. Was offline eingetragen wird, kommt beim nächsten Abgleich nach. Gelöschtes wird auf allen Geräten gelöscht.
- **Vorrat** als To-do-Liste `todo.tellerflamme_vorrat`: offen = da, Beschreibung „fast leer“ = fast leer, abgehakt = leer.
- **Einkaufsliste** `todo.tellerflamme_einkauf`: alles, was leer oder fast leer ist. Abhaken heißt gekauft, dann steht es im Vorrat wieder auf „da“.
- **Sensoren** (die Werte liefert die App bei jedem Abgleich):
  - `sensor.tellerflamme_rezeptvorschlag`: bestes Rezept aus dem Vorrat. In den Attributen stehen bis zu 5 Rezepte mit fehlenden Zutaten und den Nährstoffen, gegen die sie helfen, außerdem Lebensmittel aus dem Vorrat gegen die Lücken.
  - `sensor.tellerflamme_vitaminluecken`: die drei Nährstoffe mit der größten Lücke (Schnitt der letzten 7 Tage).
  - `sensor.tellerflamme_kalorien_heute`, `sensor.tellerflamme_streak`, `sensor.tellerflamme_vorrat_anzahl`
- **Aktionen:** `tellerflamme.vorrat_setzen` (name, status: da / wenig / leer) und `tellerflamme.vorrat_entfernen` (name).

## Mehrere Personen

Jede Person in Home Assistant hat eigene Daten: Tagebuch, Vorrat, Einkaufsliste, Rezepte, Ziele und Sensoren. Welche Person es ist, erkennt die Erweiterung am Zugangs-Token, das in der App eingetragen ist. Also: Jede Person erstellt den Token in **ihrem eigenen** Home-Assistant-Profil. In der App steht unter *Ziele → Home Assistant*, als wer sie verbunden ist.

- Pro Person gibt es ein Gerät „Tellerflamme <Name>“ mit eigenen Entitäten, z. B. `todo.tellerflamme_vorrat_sophie` und `sensor.tellerflamme_kalorien_heute_sophie`.
- Die Hauptperson behält die IDs ohne Namen (`todo.tellerflamme_vorrat` usw.), damit bestehende Dashboards und Automationen weiterlaufen.
- Daten aus der Zeit vor Version 1.1 gehören der Hauptperson. Das ist anfangs der Besitzer von Home Assistant. Ändern unter *Einstellungen → Geräte & Dienste → Tellerflamme → Konfigurieren*, am besten bevor sich die anderen Geräte neu verbinden.
- Bei `tellerflamme.vorrat_setzen` und `tellerflamme.vorrat_entfernen` kann man mit `person: Sophie` angeben, wessen Vorrat gemeint ist. Ohne Angabe: wer die Aktion ausführt, sonst die Hauptperson.

Die Daten liegen in `.storage/tellerflamme` und sind damit in jedem Home-Assistant-Backup enthalten.

## Installieren

**Mit HACS:** HACS → oben rechts ⋮ → *Benutzerdefinierte Repositories* → `https://github.com/legolas06/essen`, Typ *Integration* → „Tellerflamme“ herunterladen → Home Assistant neu starten.

**Ohne HACS:** den Ordner `custom_components/tellerflamme` nach `/config/custom_components/tellerflamme` kopieren (z. B. mit dem Add-on „File editor“ oder „Samba share“) und Home Assistant neu starten.

Danach: *Einstellungen → Geräte & Dienste → Integration hinzufügen → Tellerflamme*.

## App verbinden

1. In Home Assistant unten links auf dein Profil → *Sicherheit* → *Langlebige Zugangs-Token* → *Token erstellen*, Namen z. B. „Tellerflamme“. Den Token kopieren (er wird nur einmal angezeigt).
2. In der App: *Ziele* → *Home Assistant* → Adresse und Token eintragen → *Speichern und testen*.
3. Auf jedem Gerät dasselbe machen. Am besten zuerst auf dem Gerät mit den meisten Einträgen: Beim ersten Abgleich eines Geräts gewinnen bei den Zielen die Werte, die schon in Home Assistant liegen.

**Welche Adresse?**
- Daheim im WLAN: `http://homeassistant.local:8123` oder `http://<IP>:8123`. Das geht in der Android- und iOS-App (ab der APK mit diesem Stand, weil Android http sonst blockiert).
- Von unterwegs: eine https-Adresse, z. B. von Nabu Casa (`https://xxxx.ui.nabu.casa`).
- Die Webseite (`https://legolas06.github.io/Essen/`) kann nur eine https-Adresse erreichen und braucht zusätzlich in der `configuration.yaml`:

```yaml
http:
  cors_allowed_origins:
    - https://legolas06.github.io
```

## Beispiele

Dashboard-Karte mit Vorschlag und Lücken:

```yaml
type: markdown
title: Heute essen
content: |
  **{{ states('sensor.tellerflamme_rezeptvorschlag') }}**
  {% for r in state_attr('sensor.tellerflamme_rezeptvorschlag', 'vorschlaege') or [] %}
  - {{ r.name }}{% if r.fehlt %} (fehlt: {{ r.fehlt | join(', ') }}){% endif %}
  {% endfor %}
  Lücken: {{ states('sensor.tellerflamme_vitaminluecken') }}
```

Dazu einfach die Karten *To-do-Liste* für `todo.tellerflamme_vorrat` und `todo.tellerflamme_einkauf`.

Per Sprache (Assist) geht ohne weitere Einrichtung z. B. „Füge Milch zu Vorrat hinzu“ oder „Füge Eier zur Einkaufsliste hinzu“.

Automation: Erinnerung, wenn abends noch viel Kalorien offen sind:

```yaml
triggers:
  - trigger: time
    at: "19:00:00"
conditions:
  - condition: template
    value_template: >
      {{ (state_attr('sensor.tellerflamme_kalorien_heute', 'ziel') | int(0))
         - (states('sensor.tellerflamme_kalorien_heute') | int(0)) > 800 }}
actions:
  - action: notify.notify
    data:
      message: "Noch viel offen heute. Vorschlag: {{ states('sensor.tellerflamme_rezeptvorschlag') }}"
```
