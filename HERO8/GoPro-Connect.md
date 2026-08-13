## What is GoPro Connect (Webcam mode) on HERO8?

Come su HERO9 (vedi [HERO9/GoPro-Connect.md](/HERO9/GoPro-Connect.md)), espone
le stesse API disponibili via WiFi ma su USB Ethernet — la camera si presenta
al computer come un piccolo adattatore di rete (CDC-ECM), non come una
webcam UVC nativa. Per questo su Linux/Mac/Windows senza il tool ufficiale
"GoPro Webcam" serve un ponte manuale (script `ffmpeg` che legge lo stream
UDP e lo inietta in un dispositivo v4l2loopback — vedi
[scripts/gopro-webcam.sh](/HERO8/scripts/gopro-webcam.sh) in questa cartella).

Verificato dal vivo il 2026-08-13 su una HERO8 Black, firmware v2.51.00.

## Setup iniziale (una tantum)

Sulla HERO8 la webcam mode nativa non ha una voce di menu dedicata
("Connessioni > Webcam" arriva solo dai modelli successivi). Va sbloccata
una volta sola:

1. Camera spenta, collega il cavo USB-C al computer
2. Tieni premuto il pulsante **Mode** (laterale, non lo shutter) per un paio
   di secondi, finche' non compare l'icona webcam/anteprima sullo schermo

**Importante**: questo gesto serve solo la *primissima volta* per abilitare
la funzione sul firmware. Nelle sessioni successive basta collegare il cavo
USB normalmente e chiamare l'endpoint `START` via rete (vedi sotto) — non
serve ripetere il gesto Mode. Lo abbiamo verificato piu' volte nella stessa
giornata di test.

## Trovare l'IP della camera

Collegando il cavo USB-C, il PC riceve un IP via DHCP dalla camera su
un'interfaccia di rete USB (su Linux tipicamente `enx<mac>`), sottorete
`172.XX.XXX.0/24`. La camera stessa si assegna sempre l'ultimo ottetto
**.51** della stessa sottorete.

Esempio (Linux):
```bash
ip -4 -br addr show | grep enx
# enx421d6c4380d6  UP  172.27.140.54/24
# -> la camera e' su 172.27.140.51
```

## Commands:

**NOTE**: comandi da inviare sull'IP con ottetto finale *.51*.

- Webcam mode START: `http://172.XX.XXX.51/gp/gpWebcam/START`
	- Risoluzioni:
	- 1080p: `http://172.XX.XXX.51/gp/gpWebcam/START?res=1080`
	- 720p: `http://172.XX.XXX.51/gp/gpWebcam/START?res=720`
	- 480p: `http://172.XX.XXX.51/gp/gpWebcam/START?res=480`
- Webcam mode STOP: `http://172.XX.XXX.51/gp/gpWebcam/STOP`
- Wide FOV: `http://172.XX.XXX.51/gp/gpWebcam/SETTINGS?fov=0`
- Linear FOV: `http://172.XX.XXX.51/gp/gpWebcam/SETTINGS?fov=4`
- Narrow FOV: `http://172.XX.XXX.51/gp/gpWebcam/SETTINGS?fov=6`
- 1 Mbps Bitrate: `http://172.XX.XXX.51/gp/gpWebcam/SETTINGS?bitrate=1000000`
- 2 Mbps Bitrate: `http://172.XX.XXX.51/gp/gpWebcam/SETTINGS?bitrate=2000000`
- 5 Mbps Bitrate: `http://172.XX.XXX.51/gp/gpWebcam/SETTINGS?bitrate=5000000`

`/gp/gpWebcam/status` esiste ma non e' affidabile: risponde sempre `{}` con
HTTP 404, indipendentemente dallo stato reale dello streaming. Per sapere se
la camera e' occupata/streaming, usare
`/gp/gpControl/command/mobile_offload/get_state` (vedi
[HERO8-Commands.md](/HERO8/HERO8-Commands.md)).

### Risposte osservate su START/STOP

```
START riuscito:  {"status": 2, "error": 0}   HTTP 200
STOP riuscito:   {"status": 1, "error": 0}   HTTP 200
START fallito:   {"status": 1, "error": N}   HTTP 500   (N osservato: 1 e 4)
```

Non abbiamo determinato il significato esatto dei codici di errore diversi
da 0. In pratica, se `START` fallisce con `error` != 0 ripetutamente anche
dopo uno `STOP` pulito, la causa piu' probabile e' che la camera e' finita
in uno stato interno inconsistente per troppe chiamate API ravvicinate nella
stessa sessione — vedi [Testing-Notes.md](/HERO8/Testing-Notes.md). La
soluzione che ha sempre funzionato: spegnimento completo e riaccensione
della camera (non basta scollegare/ricollegare il cavo USB).

## Media browsing:

JSON media list esposto su `http://172.XX.XXX.51/gp/gpMediaList`
(non testato in dettaglio in questa sessione, presente anche su HERO7/HERO9).

## Live preview

Dopo `START`, lo stream video parte su **UDP porta 8554**.

Comando VLC (dalla doc HERO9, non testato in questa sessione):
```
vlc -vvv --network-caching=300 --sout-x264-preset=ultrafast --sout-x264-tune=zerolatency --sout-x264-vbv-bufsize 0 --sout-transcode-threads 4 --no-audio udp://@:8554
```

Comando ffmpeg verificato funzionante (usato in
[scripts/gopro-webcam.sh](/HERO8/scripts/gopro-webcam.sh) per iniettare lo
stream in un device v4l2loopback):
```bash
ffmpeg -fflags nobuffer -f mpegts -probesize 5000000 -analyzeduration 5000000 \
    -i udp://0.0.0.0:8554 -f v4l2 -vf format=yuv420p /dev/videoN
```

**Nota probesize**: con `-probesize` troppo piccolo (es. 8192, valore usato
in alcune guide online) ffmpeg a volte non riesce a identificare il flusso
video H.264 (lo confonde con "Unknown: none"), riconoscendo solo l'audio
AAC. Un valore piu' alto (5 milioni) risolve il problema in modo affidabile.

Molte grazie a Daryl Stimm di GoPro per aver reso pubblica la maggior parte
di queste informazioni (via HERO9/GoPro-Connect.md), e a chi ha scritto le
guide linkate in [Testing-Notes.md](/HERO8/Testing-Notes.md) per la parte
Linux/v4l2loopback.
