## GoPro HERO8

Cameras covered: HERO8 Black

### First, a preface:

Il README principale di questo repository dice: *"For GoPro Hero8, for
GoPro Connect (Webcam Mode), use Hero9 commands; for other commands, use
Hero7 commands."* — questa cartella raccoglie in un unico posto entrambe le
cose, verificate live su hardware reale (non solo copiate/incollate), piu'
endpoint aggiuntivi mai documentati prima, trovati analizzando il firmware
ufficiale.

* [Wifi/USB Commands](/HERO8/HERO8-Commands.md) — comandi base (identici a
  HERO7) + sezione "Additional/Undocumented Commands" con quanto trovato nel
  firmware v2.51.00
* [GoPro Connect (Webcam mode)](/HERO8/GoPro-Connect.md) — come usare la
  HERO8 come webcam via USB, incluso il gesto di sblocco iniziale e come
  usarla su Linux (dove non esiste un tool ufficiale come per Windows/Mac)
* [Firmware-Endpoints.md](/HERO8/Firmware-Endpoints.md) — elenco grezzo degli
  endpoint estratti dalle stringhe del firmware, con nota di rischio per
  quelli pericolosi (factory reset, aggiornamento firmware, spegnimento)
* [Testing-Notes.md](/HERO8/Testing-Notes.md) — comportamenti/quirk osservati
  durante i test dal vivo (corruzione di stato dopo troppe chiamate
  ravvicinate, il gesto Mode che serve solo una volta, endpoint che
  rispondono 404 nonostante siano nel firmware, ecc.)
* [scripts/](/HERO8/scripts) — tool pronti all'uso:
  * `gopro-webcam.sh` — usa la HERO8 come webcam su Linux (v4l2loopback +
    ffmpeg)
  * `gopro_ctl.py` — CLI Python (nessuna dipendenza esterna) per controllare
    la camera via USB: stato, batteria, locate, modalita', scatto,
    impostazioni, zoom, webcam, WiFi/BLE scan, storage, log. Include una
    guardia di conferma per i comandi pericolosi.

### Nota sull'attivazione della webcam mode

A differenza dei modelli successivi, la HERO8 non ha una voce di menu
"Webcam" — la funzione va sbloccata una tantum tenendo premuto il pulsante
Mode con USB collegato. Dopo il primo sblocco resta attiva per sempre,
anche dopo spegnimenti/riaccensioni. Dettagli in
[GoPro-Connect.md](/HERO8/GoPro-Connect.md).

### Attenzione

Durante i test abbiamo osservato che troppe chiamate API ravvicinate (in
particolare modificando piu' impostazioni/modalita' di fila) possono mandare
la camera in uno stato interno inconsistente, fino a farla sparire
completamente dalla connessione USB. La soluzione e' sempre stata uno
spegnimento completo e riaccensione pulita. Dettagli e raccomandazioni in
[Testing-Notes.md](/HERO8/Testing-Notes.md).
