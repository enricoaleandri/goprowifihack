#!/usr/bin/env python3
"""Controllo remoto della GoPro Hero8 Black via USB (API gpControl/gpWebcam).

Uso: ./gopro_ctl.py <comando> [opzioni]

Esempi:
    ./gopro_ctl.py status
    ./gopro_ctl.py battery
    ./gopro_ctl.py locate on
    ./gopro_ctl.py mode photo
    ./gopro_ctl.py shutter start
    ./gopro_ctl.py setting 2 9          # risoluzione video 1080p
    ./gopro_ctl.py webcam start --res 720
    ./gopro_ctl.py webcam stop
    ./gopro_ctl.py zoom 50
    ./gopro_ctl.py wifi scan
    ./gopro_ctl.py ble scan
    ./gopro_ctl.py raw /gp/gpControl/command/sub_mode?mode=0&sub_mode=1

Trova automaticamente l'IP della GoPro cercando l'interfaccia di rete USB
(enx*) e assumendo che la camera sia sull'ultimo indirizzo .51 della stessa
sottorete. Puoi forzare l'IP con --ip o la variabile d'ambiente GOPRO_IP.
"""
import argparse
import ipaddress
import json
import subprocess
import sys
import urllib.error
import urllib.request

# Comandi volutamente ESCLUSI da questo tool perche' pericolosi/irreversibili:
# system/factory/reset, system/factory_reset, fwupdate/download/*,
# system/shutdown, wireless/ap/control.
# Restano disponibili solo passando il path a mano con `raw`, a proprio rischio.
DANGEROUS_SUBSTRINGS = [
    "factory/reset", "factory_reset", "fwupdate", "system/shutdown",
    "wireless/ap/control",
]


def find_gopro_ip():
    try:
        out = subprocess.run(
            ["ip", "-4", "-br", "addr", "show"],
            capture_output=True, text=True, timeout=5, check=True,
        ).stdout
    except Exception:
        return None
    for line in out.splitlines():
        parts = line.split()
        if not parts or not parts[0].startswith("enx"):
            continue
        for p in parts[2:]:
            addr = p.split("/")[0]
            try:
                ip = ipaddress.ip_address(addr)
            except ValueError:
                continue
            octets = str(ip).split(".")
            octets[-1] = "51"
            return ".".join(octets)
    return None


class GoPro:
    def __init__(self, ip):
        self.ip = ip

    def _check_dangerous(self, path):
        for s in DANGEROUS_SUBSTRINGS:
            if s in path:
                print(f"Endpoint '{path}' e' nella lista dei comandi pericolosi.")
                answer = input("Scrivi CONFERMO per procedere comunque: ")
                if answer != "CONFERMO":
                    print("Annullato.")
                    sys.exit(1)

    def get(self, path, timeout=6):
        if not path.startswith("/"):
            path = "/" + path
        self._check_dangerous(path)
        url = f"http://{self.ip}{path}"
        req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode(errors="replace")
                code = resp.status
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            code = e.code
        except urllib.error.URLError as e:
            print(f"Errore di connessione a {url}: {e}", file=sys.stderr)
            sys.exit(1)
        return code, body

    def call(self, path, quiet=False):
        code, body = self.get(path)
        if not quiet:
            print(f"GET {path} -> HTTP {code}")
            print(body.strip() or "<vuoto>")
        return code, body

    def json_call(self, path):
        code, body = self.get(path)
        try:
            return code, json.loads(body)
        except json.JSONDecodeError:
            return code, None


def cmd_status(gp, args):
    code, data = gp.json_call("/gp/gpControl/status")
    if data is None:
        print(f"Errore (HTTP {code})")
        return
    print(json.dumps(data, indent=2))


def cmd_battery(gp, args):
    code, data = gp.json_call("/gp/gpControl/command/mobile_offload/get_state")
    if data is None:
        print(f"Errore (HTTP {code})")
        return
    print(f"Batteria OK:   {'si' if data.get('battery_ok') else 'no'}")
    print(f"SD card OK:    {'si' if data.get('sd_card_ok') else 'no'}")
    print(f"Camera busy:   {'si' if data.get('camera_busy') else 'no'}")
    print(f"Nuovi media:   {'si' if data.get('new_media') else 'no'}")


def cmd_locate(gp, args):
    p = "1" if args.state == "on" else "0"
    gp.call(f"/gp/gpControl/command/system/locate?p={p}")


def cmd_beacon(gp, args):
    p = "1" if args.state == "on" else "0"
    gp.call(f"/gp/gpControl/command/system/enable_beacon?p={p}")


def cmd_mode(gp, args):
    modes = {"video": 0, "photo": 1, "multishot": 2}
    gp.call(f"/gp/gpControl/command/mode?p={modes[args.mode]}")


def cmd_shutter(gp, args):
    p = "1" if args.state == "start" else "0"
    gp.call(f"/gp/gpControl/command/shutter?p={p}")


def cmd_setting(gp, args):
    gp.call(f"/gp/gpControl/setting/{args.id}/{args.value}")


def cmd_zoom(gp, args):
    gp.call(f"/gp/gpControl/command/digital_zoom?range_pcnt={args.percent}")


def cmd_submode(gp, args):
    gp.call(f"/gp/gpControl/command/sub_mode?mode={args.mode}&sub_mode={args.sub_mode}")


def cmd_protune_reset(gp, args):
    suffix = "" if args.target == "generic" else f"{args.target}/"
    gp.call(f"/gp/gpControl/command/{suffix}protune/reset".replace("generic/", ""))


def cmd_webcam(gp, args):
    if args.action == "start":
        gp.call(f"/gp/gpWebcam/START?res={args.res}")
    elif args.action == "stop":
        gp.call("/gp/gpWebcam/STOP")
    elif args.action == "settings":
        gp.call(f"/gp/gpWebcam/SETTINGS?fov={args.fov}&bitrate={args.bitrate}")


def cmd_wifi(gp, args):
    if args.action == "scan":
        gp.call("/gp/gpControl/command/wireless/ssid/scan?p=1")
    elif args.action == "list":
        gp.call("/gp/gpControl/command/wireless/ssid/list")


def cmd_ble(gp, args):
    paths = {
        "scan": "/gp/gpControl/command/ble/scan?p=1",
        "scan-list": "/gp/gpControl/command/ble/scan/list",
        "status": "/gp/gpControl/command/ble/pair/status",
        "whitelist": "/gp/gpControl/command/ble/whitelist/list",
        "configure": "/gp/gpControl/command/ble/configure",
    }
    gp.call(paths[args.action])


def cmd_storage(gp, args):
    paths = {
        "delete-last": "/gp/gpControl/command/storage/delete/last",
        "delete-all": "/gp/gpControl/command/storage/delete/all",
        "tag-moment": "/gp/gpControl/command/storage/tag_moment",
    }
    gp.call(paths[args.action])


def cmd_transcode_history(gp, args):
    gp.call("/gp/gpControl/command/transcode/history")


def cmd_logs(gp, args):
    if args.action == "list":
        gp.call("/gp/gpControl/command/system/logs_list")
    elif args.action == "clear":
        gp.call("/gp/gpControl/command/system/logs_clear")


def cmd_raw(gp, args):
    gp.call(args.path)


def build_parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--ip", default=None, help="IP della GoPro (default: auto-rilevato o $GOPRO_IP)")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Stato completo della camera (JSON)").set_defaults(func=cmd_status)
    sub.add_parser("battery", help="Batteria/SD/stato sintetico").set_defaults(func=cmd_battery)

    sp = sub.add_parser("locate", help="Beacon locate (beep+LED)")
    sp.add_argument("state", choices=["on", "off"])
    sp.set_defaults(func=cmd_locate)

    sp = sub.add_parser("beacon", help="Bluetooth beacon on/off")
    sp.add_argument("state", choices=["on", "off"])
    sp.set_defaults(func=cmd_beacon)

    sp = sub.add_parser("mode", help="Cambia modalita'")
    sp.add_argument("mode", choices=["video", "photo", "multishot"])
    sp.set_defaults(func=cmd_mode)

    sp = sub.add_parser("shutter", help="Avvia/ferma scatto o registrazione")
    sp.add_argument("state", choices=["start", "stop"])
    sp.set_defaults(func=cmd_shutter)

    sp = sub.add_parser("setting", help="Imposta un parametro (vedi gopro-hero8-api-endpoints.md)")
    sp.add_argument("id", type=int)
    sp.add_argument("value", type=int)
    sp.set_defaults(func=cmd_setting)

    sp = sub.add_parser("zoom", help="Zoom digitale")
    sp.add_argument("percent", type=int, choices=range(0, 101), metavar="0-100")
    sp.set_defaults(func=cmd_zoom)

    sp = sub.add_parser("submode", help="Imposta sotto-modalita'")
    sp.add_argument("mode", type=int)
    sp.add_argument("sub_mode", type=int)
    sp.set_defaults(func=cmd_submode)

    sp = sub.add_parser("protune-reset", help="Reset protune")
    sp.add_argument("target", choices=["generic", "video", "photo", "multi_shot"], default="generic", nargs="?")
    sp.set_defaults(func=cmd_protune_reset)

    sp = sub.add_parser("webcam", help="Modalita' webcam")
    wsub = sp.add_subparsers(dest="action", required=True)
    st = wsub.add_parser("start")
    st.add_argument("--res", default="720", choices=["480", "720", "1080"])
    wsub.add_parser("stop")
    se = wsub.add_parser("settings")
    se.add_argument("--fov", default="0", choices=["0", "4", "6"])
    se.add_argument("--bitrate", default="2000000")
    sp.set_defaults(func=cmd_webcam)

    sp = sub.add_parser("wifi", help="WiFi della camera")
    sp.add_argument("action", choices=["scan", "list"])
    sp.set_defaults(func=cmd_wifi)

    sp = sub.add_parser("ble", help="Bluetooth")
    sp.add_argument("action", choices=["scan", "scan-list", "status", "whitelist", "configure"])
    sp.set_defaults(func=cmd_ble)

    sp = sub.add_parser("storage", help="Operazioni storage")
    sp.add_argument("action", choices=["delete-last", "delete-all", "tag-moment"])
    sp.set_defaults(func=cmd_storage)

    sub.add_parser("transcode-history", help="Storico transcodifiche").set_defaults(func=cmd_transcode_history)

    sp = sub.add_parser("logs", help="Log di sistema")
    sp.add_argument("action", choices=["list", "clear"])
    sp.set_defaults(func=cmd_logs)

    sp = sub.add_parser("raw", help="Chiama un path qualsiasi (es. /gp/gpControl/command/...)")
    sp.add_argument("path")
    sp.set_defaults(func=cmd_raw)

    return p


def main():
    import os
    parser = build_parser()
    args = parser.parse_args()

    ip = args.ip or os.environ.get("GOPRO_IP") or find_gopro_ip()
    if not ip:
        print("Impossibile determinare l'IP della GoPro. Usa --ip o esporta GOPRO_IP.", file=sys.stderr)
        sys.exit(1)

    gp = GoPro(ip)
    args.func(gp, args)


if __name__ == "__main__":
    main()
