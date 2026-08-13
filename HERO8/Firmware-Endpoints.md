# Endpoint API GoPro Hero8 Black (estratti dal firmware ufficiale v2.51.00)

Estratti con `strings` su `DATA.bin` dentro l'UPDATE.zip firmware ufficiale GoPro.
Base URL: `http://172.27.140.51` (o l'IP che la GoPro assume sull'interfaccia USB `enx*`).
La maggior parte va sotto `/gp/gpControl/` + il percorso indicato.

## Gia' testati e confermati oggi (sicuri)

- `gp/gpControl/status`
- `gp/gpWebcam/START?res=720`, `STOP`, `SETTINGS?fov=X&bitrate=Y`
- `gp/gpControl/command/system/locate?p=1/0`
- `gp/gpControl/command/digital_zoom?range_pcnt=N`
- `gp/gpControl/command/mode?p=0/1/2`
- `gp/gpControl/command/shutter?p=1/0` (fallisce senza SD, atteso)
- `gp/gpControl/setting/<id>/<valore>`
- `gp/gpControl/command/storage/delete/last`, `/all`
- `gp/gpControl/command/wireless/ssid/scan`, `/list`
- `gp/gpControl/command/ble/scan`
- `gp/gpControl/command/transcode/request`

## Nuovi prefissi di primo livello (oltre a gpControl/gpWebcam)

- `/gp/gpBacpac` — gestione modulo batteria esterna (Bacpac)
- `/gp/gpCamera` — handler camera generico
- `/gp/gpCert` — verifica certificati
- `/gp/gpEMS` — sconosciuto (Enhanced Media Sharing?)
- `/gp/gpMediaList`, `/gpMediaListEx` — lista file su SD
- `/gp/gpMediaMetadata`, `/gpMediaMetadata2` — metadati file
- `/gp/gpMediaOp` — operazioni su file media
- `/gp/gpSoftUpdate`, `/gp/gpUpdate` — aggiornamento software
- `/gp/gpTurbo` — sconosciuto (trasferimento rapido media?)

## Nuovi comandi SICURI da testare (sola lettura o triviali)

- `command/ble/pairing_available` — legge se il pairing BT e' disponibile
- `command/ble/pairing_phase` — stato fase pairing
- `command/ble/pair/status` — stato pairing BLE
- `command/ble/scan/list` — lista risultati scan BLE
- `command/mobile_offload/get_state` — stato offload media verso app
- `command/system/get_beacon` — stato beacon Bluetooth
- `command/system/logs_list` — lista log
- `command/system/suspend_resume_state` — stato sospensione (solo lettura probabile)
- `command/transcode/history` — storico transcodifiche
- `command/liveview/exposure_mode` — modalita' esposizione live view (con parametro)
- `command/wireless/ap/ssid` — leggere/impostare nome rete WiFi camera

## Nuovi comandi da testare CON CAUTELA (modificano stato ma reversibili)

- `command/button_set` — configurazione pulsanti
- `command/set_client_info`, `command/set_mode`, `command/set_preset`
- `command/setup/date_time` — imposta data/ora camera
- `command/onscreen_shortcuts_reset`
- `command/photo_timer`, `command/sub_mode`
- `command/*/protune/reset` (multi_shot, photo, video, protune generico)
- `command/storage/tag_moment/playback`, `/playback/photo`
- `command/storage/delete/group`
- `command/system/enable_beacon`, `set_beacon`
- `command/system/notify_event`
- `command/system/logs_clear` — cancella i log (minore)
- `command/wireless/pair/cancel`, `/complete`
- `command/wireless/rc/pair`, `/rc/pair/cancel`
- `command/wireless/band/select`
- `command/wirelessOffload/pause`, `/start`, `/stop`
- `command/wireless/ssid/delete`, `/save`
- `command/ble/configure`, `/control`, `/pair/cancel`
- `command/ble/whitelist/configure`, `/device`, `/list`

## ⚠️ PERICOLOSI — NON testare senza motivo preciso

- `command/system/factory/reset`, `command/system/factory_reset` — **azzera tutte le impostazioni della camera**
- `command/fwupdate/download/start`, `/cancel`, `/done` — **avvia procedura di aggiornamento firmware reale**, interromperla puo' danneggiare la camera
- `command/system/shutdown` — spegne subito la camera (chiude la sessione USB)
- `command/wireless/ap/control` — puo' disattivare il WiFi della camera stessa
- `command/rc/pair` — avvia pairing con un vero telecomando

## Risultati test dal vivo (13/08/2026)

Tutti testati uno alla volta con pausa, connessione rimasta stabile per l'intera sessione.

| Endpoint | Esito |
|---|---|
| `ble/pairing_available` | 200 `{}` |
| `ble/pairing_phase` | 500 (serve stato attivo) |
| `ble/pair/status` | 200 `{"pairing_status":0}` |
| `ble/scan/list` | 200 lista vuota |
| `ble/configure` | 200 `{"auto_connect":1}` |
| `ble/control` | 500 (serve parametro) |
| `ble/pair/cancel` | 500 (serve stato attivo) |
| `ble/whitelist/list` | 200 lista vuota |
| `mobile_offload/get_state` | 200 — **utile**: batteria/sd/camera_busy in un colpo |
| `system/get_beacon` | 200 `{"uuid":..,"major":0,"minor":0}` |
| `system/enable_beacon?p=0` | 200 `{}` |
| `system/logs_list` | 500 |
| `system/logs_clear` | 500 (serve parametro) |
| `system/suspend_resume_state` | 500 (serve parametro) |
| `transcode/history` | 200 `{"history":[]}` |
| `liveview/exposure_mode` | 500 (serve parametro) |
| `wireless/ap/ssid` | 500 (serve parametro per impostare) |
| `sub_mode?mode=X&sub_mode=Y` | 200 — funziona |
| `protune/reset`, `video/protune/reset` | 200 |
| `photo/protune/reset`, `multi_shot/protune/reset` | 500 (serve essere in quella modalita') |
| `onscreen_shortcuts_reset` | 200 |
| `photo_timer` | 500 (serve parametro) |
| `wirelessOffload/pause`, `/stop` | **404 — non esiste con questo path** |
| `storage/tag_moment/playback[/photo]` | 500 (serve parametro) |
| `storage/delete/group` | 500 (serve parametro) |
| `wireless/pair/cancel`, `rc/pair/cancel` | 200 `{}` |
| `set_mode?p=0` | 500 |
| `wireless/band/select` | 500 (serve parametro) |
| `wireless/ssid/delete`, `/save` | 500 (serve parametro) |

Nessun test eseguito sui comandi pericolosi (factory reset, fwupdate, shutdown, ap control) — esclusi di proposito.

## Nota
Fonte firmware: `HD8.01-02_51_00-20220324-firmware.zip`
(https://github.com/KonradIT/gopro-firmware-archive)
