"""Self-checks that do not need a network, a key, or a browser.

    cd week8
    python code/check_sim.py

What is checked, and why each one matters:

  A  the world's rules      a refusal is a rule, not a mood. If the chart-room
                            door can be pushed open without being sent, the
                            whole lesson about rank and standing orders is gone.
  B  the character's JSON   the model proposes; the world must survive a reply
                            that is wrapped in a code fence, has an unknown
                            action, is too long, or talks about 1912 from 2026.
  C  no key, no pretending  without DEEPSEEK_API_KEY the sim must either replay
                            a recording and say so, or fail loudly.
  D  the knowledge base     every quotation must be findable in a source that is
                            on disk, or the fact does not load.
  E  the prompt's hygiene   the court's finding must never be inside the
                            character's prompt; only what he could perceive.
  F  the receipt            the cost printed on the page is computed from the
                            usage the API returns, so the arithmetic is tested.
  G  the server             one HTTP round trip: state in, action out.
"""

import json
import os
import sys
import threading
import traceback
from datetime import datetime, timezone
from http.client import HTTPConnection
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "sim"))
sys.path.insert(0, str(ROOT / "data"))

import model      # noqa: E402
import stone      # noqa: E402
import world      # noqa: E402

PASS, FAIL = [], []


def check(name):
    def wrap(function):
        try:
            function()
            PASS.append(name)
            print("  PASS  %s" % name)
        except Exception as exc:                      # noqa: BLE001
            FAIL.append((name, exc))
            print("  FAIL  %s\n        %s: %s" % (name, type(exc).__name__, exc))
            if os.environ.get("WEEK8_TRACE"):
                traceback.print_exc()
        return function
    return wrap


def fresh():
    return world.Game(kb=stone.load_kb())


def expect_refused(game, action, needle=""):
    try:
        game.act(action)
    except world.Refused as exc:
        assert needle.lower() in str(exc).lower(), \
            "refusal did not mention %r: %s" % (needle, exc)
        return
    raise AssertionError("expected a refusal for %r" % (action,))


# --------------------------------------------------------------------- A
@check("A1 the watch opens at 00:15 on the bridge")
def _():
    game = fresh()
    state = game.public()
    assert state["clock"] == "00:15", state["clock"]
    assert state["place"] == "bridge"
    assert state["log"] == [] and state["rockets"] == 0


@check("A2 the chart room is shut until you are sent")
def _():
    game = fresh()
    expect_refused(game, {"action": "walk", "to": "chart_room"}, "海图室")
    game.advance(110)          # past 2 o'clock: Stone sends the apprentice down
    assert game.sent_below, "the 2 a.m. beat did not send the apprentice"
    game.act({"action": "walk", "to": "chart_room"})
    assert game.place == "chart_room"


@check("A3 looking at something that is not there is refused, with the list")
def _():
    game = fresh()
    expect_refused(game, {"action": "look", "target": "engine"}, "看不到")


@check("A4 the scrap log holds eight lines; you must cross one out")
def _():
    game = fresh()
    for index in range(world.MAX_LOG):
        game.act({"action": "write", "text": "line %d, bearing S.S.E." % index})
    assert len(game.log) == world.MAX_LOG
    expect_refused(game, {"action": "write", "text": "one more"}, "满了")
    game.act({"action": "cross", "line": "3"})
    game.act({"action": "write", "text": "replacement"})
    assert len(game.log) == world.MAX_LOG and game.log[-1]["text"] == "replacement"


@check("A5 rockets fire on the world's clock, not the player's")
def _():
    game = fresh()
    game.advance(50)                      # to 01:05: five rockets, no more
    assert game.rockets == 5, game.rockets
    assert game.seen_rockets == 5
    before = game.seen_rockets
    game.sent_below = True                # pretend Stone sent him down early
    game.act({"action": "walk", "to": "chart_room"})
    assert game.place == "chart_room"
    game.advance(45)                      # the last three rockets fire meanwhile
    assert game.rockets == 8, game.rockets
    assert game.seen_rockets == before, "the chart room has no view of the sky"


@check("A6 the report to the master happens once, and only when sent")
def _():
    game = fresh()
    game.advance(110)
    game.act({"action": "walk", "to": "chart_room"})
    game.act({"action": "report"})
    assert game.reported_to_master
    expect_refused(game, {"action": "report"}, "已经报告过")


@check("A7 the watch ends at 02:20 and says so")
def _():
    game = fresh()
    game.advance(200)
    assert game.t == world.END, game.t
    assert game.ended
    expect_refused(game, {"action": "wait"}, "结束")


@check("A8 you cannot talk to a man who is on another deck")
def _():
    game = fresh()
    game.act({"action": "walk", "to": "foredeck"})
    expect_refused(game, {"action": "say", "text": "Sir?"}, "桥楼")


@check("A9 a number the player asserts is checked against the world's count")
def _():
    game = fresh()
    game.advance(50)                      # five rockets have gone up
    assert game.rockets == 5
    original = stone.respond
    stone.respond = lambda g, text: {"say": "", "zh": "", "act": "speak", "why": "",
                                     "flags": [], "source": "test"}
    try:
        game.act({"action": "say", "text": "Seven now, sir."})
    finally:
        stone.respond = original
    assert game.claims[-1] == {"time": "1.05", "said": 7, "true": 5}, game.claims
    assert world.rocket_claim("That is five rockets, sir.") == 5
    assert world.rocket_claim("Eight now, sir.") == 8
    assert world.rocket_claim("She looks very queer out of the water.") is None


# --------------------------------------------------------------------- B
@check("B1 a code-fenced reply is read as JSON")
def _():
    parsed = stone.parse('```json\n{"say":"Very well.","say_zh":"好。","act":"observe","why":"看着"}\n```')
    assert parsed["say"] == "Very well." and parsed["act"] == "observe"


@check("B2 an unknown action becomes 'speak'; a long reply is cut")
def _():
    parsed = stone.parse(json.dumps({"say": "word " * 100, "act": "teleport", "why": "x"}))
    assert parsed["act"] == "speak" and parsed["truncated"]


@check("B3 hindsight is flagged, and ice is not hindsight")
def _():
    assert stone.HINDSIGHT.search("The Titanic is sinking, sir.")
    assert stone.HINDSIGHT.search("they are distress signals")
    assert not stone.HINDSIGHT.search("There is field ice all round us.")
    assert not stone.HINDSIGHT.search("I have never seen company's signals like them.")


@check("B4 Stone cannot send you down before there is anything to report")
def _():
    game = fresh()
    reply = {"say": "Go down.", "say_zh": "", "act": "send_down", "why": "",
             "flags": [], "source": "test"}
    stone._apply(game, reply)
    assert not game.sent_below and reply["refusal"]


@check("B5 after three rockets his 'send down' happens, and is marked as a divergence")
def _():
    game = fresh()
    game.advance(75)
    assert game.rockets >= 3
    reply = {"say": "Go down and wake him.", "say_zh": "", "act": "send_down", "why": "",
             "flags": [], "source": "test"}
    stone._apply(game, reply)
    assert game.sent_below and game.divergence


# --------------------------------------------------------------------- C
@check("C1 with no key and no recording, the character refuses to answer")
def _():
    saved = os.environ.pop("DEEPSEEK_API_KEY", None)
    saved_mode = os.environ.pop("WEEK8_MODE", None)
    saved_fixture = stone.FIXTURE_PATH
    stone.FIXTURE_PATH = Path("does-not-exist.json")
    try:
        game = fresh()
        try:
            stone.respond(game, "Sir?")
        except (stone.FixtureMiss, model.ModelError):
            return
        raise AssertionError("the sim answered without a model or a recording")
    finally:
        stone.FIXTURE_PATH = saved_fixture
        if saved is not None:
            os.environ["DEEPSEEK_API_KEY"] = saved
        if saved_mode is not None:
            os.environ["WEEK8_MODE"] = saved_mode


@check("C2 WEEK8_MODE=deepseek without a key is an error, not a fallback")
def _():
    saved = os.environ.pop("DEEPSEEK_API_KEY", None)
    os.environ["WEEK8_MODE"] = "deepseek"
    try:
        try:
            stone.respond(fresh(), "Sir?")
        except model.ModelError:
            return
        raise AssertionError("a missing key was papered over")
    finally:
        if saved is not None:
            os.environ["DEEPSEEK_API_KEY"] = saved
        os.environ.pop("WEEK8_MODE", None)


# --------------------------------------------------------------------- D
@check("D1 every fact's quotation is on disk, and the locator agrees")
def _():
    import contextlib
    import io
    import verify_kb
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = verify_kb.main([])
    if code != 0:
        print(buffer.getvalue())
    assert code == 0, "verify_kb.py reported failures"


# --------------------------------------------------------------------- E
@check("E1 the court's finding is not in the character's prompt")
def _():
    facts = stone.load_kb()
    messages = stone.build_messages(fresh(), "Sir?", facts)
    system = messages[0]["content"]
    assert len(system) > 800, "the prompt is suspiciously thin"
    for fact in facts.values():
        if "later" in fact["who"]:
            assert fact["text"] not in system, "prompt leaks the court's fact %r" % fact["id"]
    for word in ("titanic", "carpathia", "might have saved", "the court found"):
        assert word not in system.lower(), "prompt leaks %r" % word


@check("E2 only facts marked for him are sent, each with a locator")
def _():
    facts = stone.load_kb()
    kept = [f for f in facts.values() if "stone" in f["who"]]
    assert kept and all("later" not in f["who"] for f in kept)
    assert all(f["locator"] for f in kept)


# --------------------------------------------------------------------- F
@check("F1 the receipt is arithmetic, not a guess")
def _():
    usage = {"prompt_tokens": 1000, "completion_tokens": 100,
             "prompt_cache_hit_tokens": 0, "prompt_cache_miss_tokens": 1000}
    off = model.price(usage, "deepseek-flash", datetime(2026, 10, 7, 12, 0, tzinfo=timezone.utc))
    peak = model.price(usage, "deepseek-flash", datetime(2026, 10, 7, 2, 0, tzinfo=timezone.utc))
    assert off["rate"] == "off-peak" and peak["rate"] == "peak"
    assert abs(off["usd"] - 0.00021) < 1e-9, off
    assert abs(peak["usd"] - 0.00042) < 1e-9, peak


# --------------------------------------------------------------------- G
@check("G1 one HTTP round trip: state, action, refusal, ending")
def _():
    os.environ["WEEK8_MODE"] = "fixture"
    import server
    server.Handler.log_message = lambda *args, **kwargs: None   # keep the test quiet
    httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection("127.0.0.1", port, timeout=10)
        conn.request("GET", "/api/state")
        reply = conn.getresponse()
        state = json.loads(reply.read().decode("utf-8"))
        assert reply.status == 200 and state["clock"] == "00:15", state
        conn.request("POST", "/api/act", json.dumps({"action": "look", "target": "light"}),
                     {"Content-Type": "application/json"})
        reply = conn.getresponse()
        payload = json.loads(reply.read().decode("utf-8"))
        assert reply.status == 200 and payload["state"]["clock"] != "00:15", payload
        conn.request("POST", "/api/act", json.dumps({"action": "walk", "to": "chart_room"}),
                     {"Content-Type": "application/json"})
        reply = conn.getresponse()
        payload = json.loads(reply.read().decode("utf-8"))
        assert reply.status == 409 and payload["refused"], payload
        conn.request("GET", "/api/ending")
        reply = conn.getresponse()
        ending = json.loads(reply.read().decode("utf-8"))
        assert reply.status == 200 and "court.saved" in ending["facts"], ending
        server.GAME.reset()
    finally:
        httpd.shutdown()
        os.environ.pop("WEEK8_MODE", None)


if __name__ == "__main__":
    print("=" * 74)
    print("  self-checks, no network and no key")
    print("=" * 74)
    print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
    for name, exc in FAIL:
        print("  - %s: %s" % (name, exc))
    sys.exit(1 if FAIL else 0)
