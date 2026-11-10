"""Konstanten für Tellerflamme."""

DOMAIN = "tellerflamme"
STORAGE_KEY = "tellerflamme"
STORAGE_VERSION = 1
SIGNAL_UPDATE = "tellerflamme_update"
SIGNAL_NEW_USER = "tellerflamme_new_user"

# Vorrat-Status, so wie die App sie speichert
ST_DA = "da"
ST_WENIG = "wenig"
ST_LEER = "leer"
STATUSES = (ST_DA, ST_WENIG, ST_LEER)
STATUS_LABEL = {ST_DA: "da", ST_WENIG: "fast leer", ST_LEER: "leer"}
