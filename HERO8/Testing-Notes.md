## Note di testing — sessione 2026-08-13

Camera: GoPro HERO8 Black, firmware v2.51.00. Collegamento: USB-C (GoPro
Connect mode), nessuna microSD inserita durante i test. Tutte le chiamate
fatte via `curl` da Linux (Ubuntu 24.04), IP camera `172.27.140.51`.

Queste note documentano comportamenti osservati che **non sono nella
documentazione ufficiale ne' in altre parti di questo repository**, utili a
chiunque smanetti ulteriormente con l'API della HERO8.

### 1. Il gesto "tieni premuto Mode" serve solo la prima volta

Per abilitare la webcam mode nativa su HERO8 serve tenere premuto il
pulsante Mode con USB collegato finche' non appare l'icona webcam (non c'e'
una voce di menu dedicata come sui modelli successivi). **Questo va fatto
una sola volta**: una volta sbloccata, la funzione resta disponibile anche
dopo spegnimento/riaccensione della camera — basta ricollegare USB e
chiamare `/gp/gpWebcam/START` via rete, senza ripetere il gesto.
Verificato piu' volte nella stessa sessione.

### 2. Troppi comandi API ravvicinati corrompono lo stato interno

Dopo una sequenza di ~15 chiamate diverse a `/gp/gpControl/command/...`
inviate subito una dopo l'altra (specialmente appena dopo aver avviato la
webcam mode con `/gp/gpWebcam/START`), la camera e' **caduta completamente
dalla connessione USB**: spariva da `lsusb`, l'interfaccia di rete USB sul
PC andava giu', nessun ping rispondeva. Serviva scollegare/ricollegare il
cavo per farla ricomparire.

In un episodio successivo, senza arrivare al crash completo, `/gp/gpControl/status`
ha restituito dati palesemente corrotti (nome modello vuoto invece di
"HERO8 Black", valori numerici enormi e privi di senso in campi che di
norma sono piccoli interi). Il sintomo si e' risolto solo con uno
spegnimento completo (tenere premuto il pulsante di accensione, non solo
scollegare USB) e riaccensione pulita — ricollegare semplicemente il cavo
non bastava.

**Lezione pratica**: quando si esplorano piu' endpoint, farlo **uno alla
volta con una pausa (~1 secondo) tra le chiamate**, e verificare la
connessione (`ping`) dopo ogni gruppetto di comandi. Con questo ritmo,
~40 comandi diversi testati in sequenza in un'altra sessione non hanno
causato nessun problema.

### 3. `/gp/gpWebcam/START` puo' fallire con codici di errore diversi anche a stato "pulito"

Osservato sia `{"status":1,"error":1}` che `{"status":1,"error":4}` (sempre
HTTP 500) in momenti diversi, anche subito dopo un `/gp/gpWebcam/STOP`
riuscito (`{"status":1,"error":0}`). Non e' stato possibile isolare la causa
esatta — sembra correlato allo stato interno accumulato da comandi
precedenti nella stessa sessione (vedi punto 2) piuttosto che a un problema
coi parametri della chiamata stessa. Il fix che ha sempre funzionato:
spegnimento completo + riaccensione della camera.

### 4. `/status` classico (stile HERO7/WiFi) non esiste su HERO8 via USB

La documentazione HERO7 usa `http://10.5.5.9/status` come endpoint di stato
rapido. Su HERO8 via USB questo risponde `404 Not Found`. L'endpoint
corretto e' `/gp/gpControl/status` (funziona sia sulla porta 80 di default
sia esplicitamente su `:8080`).

### 5. `wirelessOffload/pause|start|stop` non esiste (404)

Le stringhe `command/wirelessOffload/pause`, `/start`, `/stop` sono presenti
nel binario del firmware, ma chiamandole rispondono `404 Not Found`. O il
path e' leggermente diverso da quello letto nelle stringhe (es. prefisso
diverso), o la funzionalita' non e' esposta via HTTP su questo modello/
firmware. `command/mobile_offload/get_state` invece funziona regolarmente.

### 6. Endpoint di sola lettura utili trovati (non nella doc esistente)

`command/mobile_offload/get_state` restituisce in un colpo solo: stato
batteria (`battery_ok`), presenza SD (`sd_card_ok`), se la camera e' occupata
(`camera_busy`), se ci sono nuovi media (`new_media`). Molto piu' comodo di
`/gp/gpControl/status` per un controllo rapido "e' tutto ok?" da uno script.

### Come sono stati trovati gli endpoint aggiuntivi

Scaricato il firmware ufficiale HERO8 Black v2.51.00
(`HD8.01-02_51_00-20220324-firmware.zip`, mirror su
[gopro-firmware-archive](https://github.com/KonradIT/gopro-firmware-archive)),
estratto `DATA.bin` dall'interno dello zip (186MB), ed eseguito:

```bash
strings -n 4 DATA.bin | grep -E '^/(gp|gopro)/' | sort -u
strings -n 4 DATA.bin | grep -oE 'command/[a-zA-Z_/]+' | sort -u
```

Questo approccio (leggere le stringhe letterali compilate nel binario del
webserver della camera) e' piu' sicuro e affidabile del fuzzing attivo
contro la camera reale, e ha rivelato anche i nomi dei sorgenti interni
(es. `gpControlHP3/src/command_wireless_offload.cpp`), utili per capire come
sono organizzati i moduli di comando internamente.
