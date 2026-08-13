#!/usr/bin/env bash
set -euo pipefail

GOPRO_IP="172.27.140.51"
# Etichette SENZA spazi: il parsing dei parametri del modulo kernel con
# spazi/virgolette e' inaffidabile passando per insmod, quindi evitiamo
# del tutto il problema usando nomi senza spazi.
INTEL_LABEL="IntelMIPICamera"
CARD_LABEL="GoProWebcam"

find_device() {
    grep -l "^${1}$" /sys/devices/virtual/video4linux/*/name 2>/dev/null \
        | head -1 | sed 's#.*/\(video[0-9]*\)/name#\1#'
}

DEV="$(find_device "$CARD_LABEL" || true)"

if [ -z "$DEV" ]; then
    echo "Il device v4l2loopback per la GoPro non esiste ancora."
    echo "Ricarico il modulo v4l2loopback con 2 device (webcam integrata + GoPro)."
    echo "Chiudi prima qualsiasi app che stia usando la webcam integrata (videochiamate, Cheese, browser...)."
    read -rp "Premi invio per continuare (ti verra' chiesta la password sudo)..."

    sudo systemctl stop v4l2-relayd@default.service

    echo "Rimuovo il modulo v4l2loopback attuale..."
    sudo rmmod v4l2loopback || true

    echo "Aggiorno l'etichetta attesa da v4l2-relayd (senza spazi, stesso motivo)..."
    sudo sed -i "s/^CARD_LABEL=.*/CARD_LABEL=${INTEL_LABEL}/" /etc/v4l2-relayd /etc/v4l2-relayd.d/default.conf

    echo "Decomprimo e ricarico il modulo con insmod (bypassa /etc/modprobe.d, cosi' non si mischiano le config esistenti)..."
    KO_ZST="/lib/modules/$(uname -r)/kernel/v4l2loopback/v4l2loopback.ko.zst"
    TMP_KO="/tmp/v4l2loopback-gopro.ko"
    zstd -d -f "$KO_ZST" -o "$TMP_KO"
    sudo insmod "$TMP_KO" devices=2 "card_label=${INTEL_LABEL},${CARD_LABEL}" exclusive_caps=1,1
    rm -f "$TMP_KO"

    echo "Verifica etichette assegnate ai device:"
    for f in /sys/devices/virtual/video4linux/*/name; do echo "  $f: $(cat "$f")"; done

    echo "Riavvio v4l2-relayd per la webcam integrata..."
    sudo systemctl start v4l2-relayd@default.service
    sleep 1
    if ! systemctl is-active --quiet v4l2-relayd@default.service; then
        echo "Attenzione: v4l2-relayd@default.service non e' attivo:" >&2
        systemctl status v4l2-relayd@default.service --no-pager -l >&2 || true
    fi

    DEV="$(find_device "$CARD_LABEL" || true)"
fi

if [ -z "$DEV" ]; then
    echo "Errore: non riesco a trovare/creare il device v4l2loopback per '$CARD_LABEL'." >&2
    exit 1
fi

echo "Uso /dev/$DEV come webcam GoPro."

cleanup() {
    echo
    echo "Fermo lo stream sulla GoPro..."
    curl -s "http://${GOPRO_IP}/gp/gpWebcam/STOP" -o /dev/null || true
}
trap cleanup EXIT INT TERM

echo "Avvio lo streaming sulla GoPro (http://${GOPRO_IP}/gp/gpWebcam/START)..."
if ! curl -s -m 5 "http://${GOPRO_IP}/gp/gpWebcam/START?res=720" -o /dev/null; then
    echo "Errore: non riesco a contattare la GoPro su ${GOPRO_IP}." >&2
    echo "Controlla che sia ancora in modalita' GoPro Connect/Webcam e collegata via USB." >&2
    exit 1
fi

sleep 2

echo "Avvio ffmpeg -> /dev/$DEV  (lascia questa finestra aperta, Ctrl+C per fermare)"
ffmpeg -fflags nobuffer -f mpegts -probesize 5000000 -analyzeduration 5000000 -i udp://0.0.0.0:8554 \
    -f v4l2 -vf format=yuv420p "/dev/$DEV"
