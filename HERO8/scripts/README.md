# Script HERO8

Due tool indipendenti, nessuna dipendenza esterna oltre a quelle elencate.

## `gopro-webcam.sh`

Usa la HERO8 come webcam su Linux. Richiede `ffmpeg`, `curl`, `zstd`,
`v4l2loopback` (modulo kernel) e `v4l2loopback-utils`. La prima esecuzione
richiede `sudo` per creare un secondo device v4l2loopback dedicato (non
tocca la webcam integrata del PC, se presente); le esecuzioni successive
(fino al prossimo riavvio del PC) non richiedono piu' la password.

```bash
./gopro-webcam.sh
```

Ctrl+C per fermare lo streaming. Seleziona "GoProWebcam" come sorgente video
nell'app che vuoi usare (browser, Zoom, OBS...).

## `gopro_ctl.py`

CLI Python 3 (solo libreria standard) per controllare la camera via USB.
Auto-rileva l'IP della camera cercando l'interfaccia di rete USB (`enx*`).

```bash
./gopro_ctl.py status              # stato completo (JSON)
./gopro_ctl.py battery             # batteria/SD/camera busy, sintetico
./gopro_ctl.py locate on|off       # beep + LED per ritrovarla
./gopro_ctl.py mode video|photo|multishot
./gopro_ctl.py shutter start|stop
./gopro_ctl.py setting <id> <valore>   # vedi HERO8-Commands.md per gli id
./gopro_ctl.py zoom 0-100
./gopro_ctl.py webcam start [--res 480|720|1080]
./gopro_ctl.py webcam stop
./gopro_ctl.py wifi scan|list
./gopro_ctl.py ble scan|status|whitelist
./gopro_ctl.py raw /gp/gpControl/command/qualsiasi/path   # passthrough libero
```

I comandi pericolosi (factory reset, aggiornamento firmware, spegnimento,
disattivazione WiFi camera) sono raggiungibili solo tramite `raw` e chiedono
conferma esplicita (`CONFERMO`) prima di eseguire.
