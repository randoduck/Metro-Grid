"""Metro Grid passenger alerts: a small local helper that sends WhatsApp messages with pywhatkit.

pywhatkit drives WhatsApp Web in this computer's default browser, so messages go out from
whichever WhatsApp account is logged in to web.whatsapp.com here. The website's
"Notify passengers" button talks to this helper on http://127.0.0.1:8765.

Run:  python notify_server.py            (sends real messages)
      python notify_server.py --dry-run  (logs messages instead of sending them)

The passenger list lives in passengers.json next to this file. It is git-ignored so phone
numbers never reach the public repository; passengers.example.json shows the format.
"""
import argparse, json, pathlib, queue, re, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HERE = pathlib.Path(__file__).parent
CONFIG = HERE / "passengers.json"
PORT = 8765
LINES = {"L1": "Blue line", "L2": "Red line", "L3": "Green line", "L4": "Orange line"}
PHONE = re.compile(r"^\+91[6-9]\d{9}$")          # Indian mobile numbers only, for now

lock = threading.Lock()
jobs = queue.Queue()
log = []                                          # last few send results, shown on /status


def load():
    if CONFIG.exists():
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    return {"sender": "", "allowed_origins": ["https://metrogrid-plum.vercel.app"], "passengers": []}


def save(cfg):
    CONFIG.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def clean_phone(raw):
    digits = re.sub(r"[^\d+]", "", str(raw))
    if digits.startswith("00"): digits = "+" + digits[2:]
    if re.fullmatch(r"[6-9]\d{9}", digits): digits = "+91" + digits
    if re.fullmatch(r"91[6-9]\d{9}", digits): digits = "+" + digits
    return digits if PHONE.match(digits) else None


def mask(phone):
    return f"{phone[:3]} {phone[3:8]} •••{phone[-2:]}" if phone else ""


def origin_ok(origin, cfg):
    if not origin or origin == "null":            # file:// pages and direct tools
        return True
    host = urlparse(origin).hostname or ""
    if host in ("localhost", "127.0.0.1"):
        return True
    return origin.rstrip("/") in [o.rstrip("/") for o in cfg.get("allowed_origins", [])]


def message(alert):
    train = str(alert.get("train", "A train"))[:40]
    line = LINES.get(alert.get("line"), "")
    when = str(alert.get("when", ""))[:40]
    where = f" on the {line}" if line else ""
    return (f"Metro Grid service alert: {train}{where} has been held for a safety check on its air "
            f"compressor (alarm at {when}). Please expect a short delay on this line. "
            f"We will message you again when normal service resumes.")


def worker(dry_run):
    if not dry_run:
        import pywhatkit                          # imported here so --dry-run works without it
    while True:
        phone, text = jobs.get()
        try:
            if dry_run:
                print(f"[dry-run] to {mask(phone)}: {text}")
                result = "dry run (not sent)"
            else:
                pywhatkit.sendwhatmsg_instantly(phone, text, wait_time=20, tab_close=True, close_time=4)
                result = "sent"
        except Exception as e:                    # keep the helper alive if one send fails
            result = f"failed: {e}"
        with lock:
            log.insert(0, {"to": mask(phone), "result": result, "at": time.strftime("%H:%M:%S")})
            del log[10:]
        print(f"{mask(phone)}: {result}")
        jobs.task_done()


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        origin = self.headers.get("Origin")
        if origin and origin_ok(origin, load()):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Private-Network", "true")

    def _send(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code); self._cors()
        self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(data)))
        self.end_headers(); self.wfile.write(data)

    def _guard(self):
        if not origin_ok(self.headers.get("Origin"), load()):
            self._send(403, {"error": "This website is not allowed to use the helper."}); return False
        return True

    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()

    def do_GET(self):
        if not self._guard(): return
        if self.path != "/status": return self._send(404, {"error": "not found"})
        cfg = load()
        with lock: recent = list(log)
        self._send(200, {"ok": True, "sender": mask(cfg.get("sender", "")), "queued": jobs.qsize(), "recent": recent,
                         "passengers": [{"name": p["name"], "phone": mask(p["phone"])} for p in cfg["passengers"]]})

    def do_POST(self):
        if not self._guard(): return
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0) or b"{}")
        except ValueError:
            return self._send(400, {"error": "Bad JSON."})
        if self.path == "/passengers":
            phone = clean_phone(body.get("phone", ""))
            if not phone: return self._send(400, {"error": "Enter a 10-digit Indian mobile number (optionally with +91)."})
            name = str(body.get("name") or "Passenger").strip()[:40]
            with lock:
                cfg = load()
                if any(p["phone"] == phone for p in cfg["passengers"]): return self._send(409, {"error": "That number is already on the list."})
                cfg["passengers"].append({"name": name, "phone": phone}); save(cfg)
            return self._send(200, {"ok": True, "added": {"name": name, "phone": mask(phone)}})
        if self.path == "/notify":
            cfg = load(); text = message(body)
            for p in cfg["passengers"]: jobs.put((p["phone"], text))
            return self._send(200, {"ok": True, "queued": len(cfg["passengers"]), "message": text})
        self._send(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="log messages instead of sending them")
    args = ap.parse_args()
    if not CONFIG.exists(): save(load())
    threading.Thread(target=worker, args=(args.dry_run,), daemon=True).start()
    cfg = load()
    print(f"Metro Grid WhatsApp helper on http://127.0.0.1:{PORT}  ({'dry run' if args.dry_run else 'LIVE: messages will be sent'})")
    print(f"Sender: the WhatsApp account logged in to web.whatsapp.com in your default browser ({mask(cfg.get('sender', '')) or 'not set'})")
    print(f"Passengers: {len(cfg['passengers'])}. Keep this window open; press Ctrl+C to stop.")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
