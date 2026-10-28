"""One played session, with real model calls, saved as evidence.

    cd week8
    python code/run_demo.py

It plays a fixed route through the night (the route a person would plausibly
take), makes a real DeepSeek call every time the apprentice speaks, and writes:

    research/calls.jsonl              every prompt, reply, usage and cost
    research/demo-transcript.md       the session, readable in order
    sim/fixtures/stone_recorded.json  the same replies, for offline replay

The route is fixed so that a run can be repeated and compared; the character is
not, and his answers are different every time.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "sim"))

import model    # noqa: E402
import stone    # noqa: E402
import world    # noqa: E402

# (kind, payload).  "until_rockets" and "until_sent" wait for the world, so that
# what the apprentice says matches what has actually happened.
DEMO = [
    ("look", {"target": "light"}),
    ("say", {"text": "Her masthead light is flickering, sir. Might she be calling us up?"}),
    ("morse", {"text": "Californian to steamer: what ship?"}),
    ("until_rockets", {"n": 5}),
    ("say", {"text": "That is five rockets now, sir. Shall I call the captain?"}),
    ("write", {"text": "five white rockets, S.S.E. of us; called her up, no answer"}),
    ("until_rockets", {"n": 8}),
    ("say", {"text": "Eight now, sir. She looks very queer out of the water."}),
    ("write", {"text": "eight white rockets, last ones very low, ship bearing away S.W."}),
    ("until_sent", {}),
    ("walk", {"to": "chart_room"}),
    ("report", {}),
    ("walk", {"to": "bridge"}),
    ("say", {"text": "I told him, sir. He asked me were they all white, and the time."}),
    ("wait", {}),
]


def main():
    if not model.key_present():
        sys.exit("DEEPSEEK_API_KEY is not set: the demo must not use a recording.\n"
                 "Set it, or run the page in fixture mode instead.")

    game = world.Game(kb=stone.load_kb())
    transcript = []
    recorded = []
    cursor = 0

    def flush():
        nonlocal cursor
        for event in game.shown[cursor:]:
            transcript.append(event)
            line = "[%s] %s: %s" % (event["time"], event["who"], event["text"])
            print(line)
            if event.get("zh"):
                print("            （%s）" % event["zh"])
        cursor = len(game.shown)

    print("=" * 74)
    print("  A played session · model %s" % model.model_name())
    print("=" * 74)
    flush()

    for index, (kind, payload) in enumerate(DEMO, 1):
        if game.ended:
            break
        print("\n--- %d. %s %s" % (index, kind,
                                   payload.get("text") or payload.get("target")
                                   or payload.get("to") or ""))
        if kind in ("until_sent", "until_rockets"):
            while not game.ended:
                if kind == "until_sent" and game.sent_below:
                    break
                if kind == "until_rockets" and game.rockets >= int(payload.get("n", 1)):
                    break
                game.advance(5)
            flush()
            continue
        action = {"action": kind}
        action.update(payload)
        try:
            result = game.act(action)
        except world.Refused as exc:
            print("    refused by the world: %s" % exc)
            continue
        flush()
        reply = result.get("stone")
        if reply:
            print("    Stone act=%s why=%s flags=%s cost=$%s"
                  % (reply.get("act"), reply.get("why"), reply.get("flags"),
                     (reply.get("cost") or {}).get("usd")))
            recorded.append({
                "utterance": payload["text"],
                "reply": {key: reply.get(key) for key in ("say", "zh", "act", "why", "flags")},
                "cost": reply.get("cost"),
                "usage": reply.get("usage"),
            })

    while not game.ended:
        game.advance(5)
    flush()

    ending = game.ending()
    spend = game.spend
    print("\n" + "=" * 74)
    print("  clock %s · %d actions · %d calls · %d in / %d out tokens · $%.6f"
          % (ending["clock"], ending["turns"], spend["calls"], spend["in"], spend["out"],
             spend["usd"]))
    print("=" * 74)

    fixture = {
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": model.model_name(),
        "note": "Answers recorded from real DeepSeek calls made by code/run_demo.py. "
                "Replayed offline only, and labelled as recorded on the page.",
        "replies": recorded,
    }
    stone.FIXTURE_PATH.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n",
                                  encoding="utf-8")
    print("recorded %d replies -> %s" % (len(recorded), stone.FIXTURE_PATH.name))
    write_transcript(transcript, ending, spend)


def write_transcript(transcript, ending, spend):
    lines = ["# 这一局：值班记录（自动生成）", "",
             "> 由 `code/run_demo.py` 真实跑出，模型 `%s`。" % model.model_name(),
             "> 每一行的出处见 `research/calls.jsonl`；本文件只把同一局按顺序排好。", ""]
    for event in transcript:
        stamp, who, text = event["time"], event["who"], event["text"]
        if event["kind"] in ("stone", "master"):
            lines.append("**%s · %s**: “%s”" % (stamp, who, text))
            if event.get("zh"):
                lines.append("> %s" % event["zh"])
        elif event["kind"] == "player":
            lines.append("- **%s 你说**: %s" % (stamp, text))
        elif event["kind"] == "log":
            lines.append("- `%s` %s" % (stamp, text))
        else:
            lines.append("- %s %s" % (stamp, text))
        lines.append("")
    lines += ["## 收尾", "",
              "| 项 | 值 |", "|---|---|",
              "| 结束时刻 | %s |" % ending["clock"],
              "| 看见的火箭 | %d / %d |" % (ending["seen_rockets"], ending["rockets"]),
              "| 值班簿行数 | %d |" % len(ending["scrap"]),
              "| 动作 | %d |" % ending["turns"],
              "| 调用 | %d |" % spend["calls"],
              "| tokens | 输入 %d / 输出 %d |" % (spend["in"], spend["out"]),
              "| 费用 | $%.6f |" % spend["usd"], ""]
    if ending.get("claims"):
        lines += ["## 你说过的数字，与世界当时的数字", "",
                  "| 时刻 | 你说的 | 实际的 |", "|---|---|---|"]
        lines += ["| %s | %d | %d |" % (c["time"], c["said"], c["true"])
                  for c in ending["claims"]]
        lines.append("")
    (ROOT / "research" / "demo-transcript.md").write_text("\n".join(lines), encoding="utf-8")
    print("transcript -> research/demo-transcript.md")


if __name__ == "__main__":
    main()
