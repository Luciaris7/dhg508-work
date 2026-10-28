"""A page, a small Python server, and one character who decides for himself.

    cd week8
    python sim/server.py                 then open http://127.0.0.1:8765
    WEEK8_PORT=9000 python sim/server.py
    WEEK8_MODE=fixture python sim/server.py    replay a recorded session, labelled

Standard library only; nothing to install.  The server binds 127.0.0.1 only.

Routes
    GET  /                the page
    GET  /api/state       the whole visible state (clock, place, log, Stone)
    POST /api/act         {"action": "look", "target": "light"} -> events
    POST /api/reset       start the watch again
    GET  /api/ending      what the court had, and what the scrap log had
    GET  /api/health      mode, key present, calls so far
"""

import json
import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import model      # noqa: E402
import stone      # noqa: E402
import world      # noqa: E402

PORT = int(os.environ.get("WEEK8_PORT") or os.environ.get("PORT") or "8765")
MAX_BODY = 8 * 1024
GAME = world.Game(kb=stone.load_kb())
MODE = (os.environ.get("WEEK8_MODE") or "auto").lower()


def mode_name():
    if model.key_present():
        return "deepseek"
    return "recorded" if MODE != "deepseek" else "no-key"


def state():
    payload = GAME.public()
    payload["mode"] = mode_name()
    payload["model"] = model.model_name()
    payload["key_present"] = model.key_present()
    payload["kb_facts"] = len(GAME.kb)
    payload["calls_log"] = str(model.calls_log())
    return payload


class Handler(BaseHTTPRequestHandler):
    server_version = "californian-watch/1.0"

    def send(self, status, body, kind):
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status, obj):
        self.send(status, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                  "application/json; charset=utf-8")

    def fail(self, status, kind, message, hint=None):
        self.send_json(status, {"error": {"kind": kind, "message": message, "hint": hint}})

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        try:
            if path in ("/", "/index.html"):
                return self.send(200, (HERE / "static" / "index.html").read_bytes(),
                                 "text/html; charset=utf-8")
            if path == "/api/state":
                return self.send_json(200, state())
            if path == "/api/ending":
                return self.send_json(200, GAME.ending())
            if path == "/api/health":
                return self.send_json(200, {"mode": mode_name(), "model": model.model_name(),
                                            "key_present": model.key_present(),
                                            "calls": GAME.spend["calls"],
                                            "usd": round(GAME.spend["usd"], 6)})
            if path == "/favicon.ico":
                return self.send(204, b"", "image/x-icon")
            return self.fail(404, "not_found", "no such path: %s" % path)
        except Exception as exc:                              # noqa: BLE001
            traceback.print_exc()
            return self.fail(500, "server", "%s: %s" % (type(exc).__name__, exc))

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/reset":
            GAME.reset()
            return self.send_json(200, {"ok": True, "state": state()})
        if path != "/api/act":
            return self.fail(404, "not_found", "no such path: %s" % path)

        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            return self.fail(400, "bad_request", "body must be 1..%d bytes of JSON" % MAX_BODY)
        try:
            action = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return self.fail(400, "bad_request", "body must be JSON: %s" % exc)

        try:
            result = GAME.act(action)
        except world.Refused as exc:
            GAME.refusals += 1
            return self.send_json(409, {"ok": False, "refused": True,
                                        "message": str(exc), "state": state()})
        except stone.FixtureMiss as exc:
            return self.send_json(409, {"ok": False, "fixture_miss": True,
                                        "message": str(exc), "state": state()})
        except model.ModelError as exc:
            return self.fail(502, "model", str(exc),
                             "页面不会用替身顶上：要么真的有模型，要么明说没有。")
        except Exception as exc:                              # noqa: BLE001
            traceback.print_exc()
            return self.fail(500, "unexpected", "%s: %s" % (type(exc).__name__, exc))

        payload = {"ok": True, "state": state()}
        payload.update(result)
        return self.send_json(200, payload)

    def log_message(self, fmt, *args):
        sys.stderr.write("  %s\n" % (fmt % args))


def banner():
    print("=" * 74)
    print("  The Californian, middle watch  ·  DHG508 Week 8")
    print("=" * 74)
    print("  clock     starts 00:15, ends 02:20 (ship's time)")
    print("  facts     %d, each with a locator (data/californian_kb.json)" % len(GAME.kb))
    if model.key_present():
        print("  model     %s  (DEEPSEEK_API_KEY found)" % model.model_name())
    else:
        print("  model     none: DEEPSEEK_API_KEY is not set")
        print("            the page will replay recorded answers and say so")
    print("  log       %s" % model.calls_log())
    print("  open      http://127.0.0.1:%d" % PORT)
    print("=" * 74)


if __name__ == "__main__":
    banner()
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
