"""Mr Herbert Stone, second officer of the ss Californian — the character.

He is written from his own evidence (Day 7, Q7803-7960) and from section V of
the report.  What goes into his prompt is only what a second officer on that
bridge could perceive at that minute: the clock, where he is, who is with him,
the lights, the number of rockets he has himself seen, what he has already
reported, and what the apprentice has just said to him.  The court's finding is
never sent.  `data/californian_kb.json` marks which facts are his; the verifier
fails the build if a 'later' fact is ever handed to him.

He proposes one action.  The world decides whether it can happen.
"""

import json
import os
import re
from pathlib import Path

import model
from world import watch_time as game_watch

ROOT = Path(__file__).resolve().parent.parent
KB_PATH = ROOT / "data" / "californian_kb.json"
FIXTURE_PATH = ROOT / "sim" / "fixtures" / "stone_recorded.json"
MAX_WORDS = 60
MAX_CALLS = int(os.environ.get("WEEK8_MAX_CALLS", "30"))

ACTS = {
    "observe": "keep her under observation and say nothing more",
    "call_up": "call her up again on the Morse lamp",
    "speak": "say what you say and do nothing else",
    "send_down": "send the apprentice down to the master with what you have seen",
    "nothing": "say nothing and do nothing",
}

# A word the character could not have known on the night.  If he says it, the
# call is logged and the page says so; the text is shown, not rewritten.
HINDSIGHT = re.compile(
    r"\b(titanic|carpathia|distress|sinking|sank|sink|foundered|founder|disaster|"
    r"tragedy|lifeboat|1500|1,500)\b", re.IGNORECASE)


class FixtureMiss(Exception):
    pass


def load_kb():
    data = json.loads(KB_PATH.read_text(encoding="utf-8"))
    facts = {fact["id"]: fact for fact in data["facts"]}
    return facts


def memory(facts):
    """The facts Stone may know, as prompt lines.  No court findings."""
    return [fact for fact in facts.values()
            if "stone" in fact["who"] and "later" not in fact["who"]]


SYSTEM = """You are Mr Herbert Stone, second officer of the British steamer Californian, \
on the middle watch of the night of 14-15 April 1912. You are not a narrator and not an \
assistant: you are a man standing on a bridge in the cold, and everything you say is said \
out loud to the apprentice beside you.

WHAT YOU ARE
{identity}

WHAT YOU KNOW TONIGHT, AND NOTHING ELSE
{memory}

WHAT YOU CAN SEE
{perception}

HOW YOU BEHAVE
- You speak Edwardian deck English: short, dry, understated. No modern words. No lectures.
- You do not describe your feelings at length and you do not explain the plot.
- You may say nothing. Silence is a real answer, and often your answer.
- You do not know what that steamer is, why she is firing rockets, or whether anything has \
happened to any other ship. No news of any shipping casualty has reached this bridge tonight. \
You must not explain, guess or hint at what the rockets meant; you may only judge what you \
actually saw.
- You cannot see inside the chart room, the wireless room, or the other ship. You cannot \
know what the master is thinking.
- You are not the narrator. Do not write stage directions, do not write "I walk to the \
door and report" as though it were done: choose one action from the list and let the ship \
decide what happens.

CHOOSE ONE ACTION
{acts}

ANSWER WITH JSON ONLY, no prose, no code fences:
{{"say": "<what you say aloud this moment, at most 60 words, or an empty string>",
  "say_zh": "<the same in Chinese>",
  "act": "<one of: {act_keys}>",
  "why": "<one short sentence, in Chinese, of what you are thinking — shown to the player as your reason>"}}
"""


def _perception(game, utterance):
    place = {"bridge": "the bridge", "foredeck": "the foredeck",
             "chart_room": "the chart room"}[game.place]
    lines = ["It is %s a.m. by the wheelhouse clock. You are on %s."
             % (game_watch(game.t), place)]
    if game.place == "bridge":
        lines.append("The apprentice Gibson is on the bridge with you.")
    if game.light_visible:
        lines.append("The other steamer's masthead light is fine on the starboard beam, five "
                     "miles off; her red sidelight shows with the glasses; there is a glare of "
                     "white lights on her after deck. Her masthead light flickers.")
    if game.rockets:
        lines.append("You have counted %d white rockets from her direction; the apprentice has "
                     "seen %d of them himself." % (game.rockets, game.seen_rockets))
    else:
        lines.append("No rockets yet.")
    if game.claims and game.claims[-1]["said"] != game.claims[-1]["true"]:
        claim = game.claims[-1]
        lines.append("Careful: the apprentice has just called out %d rockets. He is wrong — you "
                     "have counted %d yourself. He may be counting the lights on her after deck "
                     "as well, or he may be excited." % (claim["said"], claim["true"]))
    if game.master_reported:
        lines.append("You have already spoken to the master by the voice pipe and he told you to "
                     "go on Morsing and to send the apprentice down with anything you get.")
    else:
        lines.append("You have not spoken to the master since he pointed the steamer out to you "
                     "and told you to report if her bearings altered or if she got any closer.")
    if game.log:
        lines.append("The apprentice has been writing in the scrap log: "
                     + " | ".join("%s %s" % (e["time"], e["text"][:60]) for e in game.log[-3:]))
    lines.append("The night is clear, the sea smooth, the ship stopped in field ice, cold.")
    lines.append("Gibson has just said to you: \"%s\"" % utterance.strip())
    return "\n".join(line for line in lines if line)


def build_messages(game, utterance, facts):
    identity = "\n".join("- " + fact["text"] for fact in memory(facts)
                         if fact["id"].endswith("identity"))
    known = "\n".join("- " + fact["text"] for fact in memory(facts)
                      if not fact["id"].endswith("identity"))
    system = SYSTEM.format(
        identity=identity or "- You are the second officer of the watch.",
        memory=known,
        perception=_perception(game, utterance),
        acts="\n".join("  " + key + ": " + text for key, text in ACTS.items()),
        act_keys=", ".join(ACTS),
    )
    return [{"role": "system", "content": system},
            {"role": "user", "content": "The apprentice is waiting. Answer as Stone, in JSON."}]


def parse(content):
    """Read the one JSON object out of a model reply, tolerating fences."""
    text = (content or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("回复里没有 JSON 对象")
        data = json.loads(text[start:end + 1])
    if not isinstance(data, dict):
        raise ValueError("JSON 不是一个对象")
    say = str(data.get("say") or "").strip()
    zh = str(data.get("say_zh") or "").strip()
    act = str(data.get("act") or "").strip().lower()
    why = str(data.get("why") or "").strip()
    words = say.split()
    truncated = len(words) > MAX_WORDS
    if truncated:
        say = " ".join(words[:MAX_WORDS]) + "…"
    if act not in ACTS:
        act = "speak"
    return {"say": say, "zh": zh, "act": act, "why": why, "truncated": truncated}


def respond(game, utterance):
    """One turn of the character.  Returns the record the page shows."""
    facts = load_kb()
    messages = build_messages(game, utterance, facts)
    kb_ids = [fact["id"] for fact in memory(facts)]
    mode = (os.environ.get("WEEK8_MODE") or "auto").lower()

    if not model.key_present():
        if mode == "deepseek":
            raise model.ModelError("WEEK8_MODE=deepseek 但没有 DEEPSEEK_API_KEY；"
                                   "拒绝用替身冒充模型。")
        reply = _replay(utterance)
        _apply(game, reply)          # a recorded reply is still executed by the world
        return reply

    if game.calls > MAX_CALLS:
        raise model.ModelError("本局调用已达上限（%d 次）；为了不烧预算，此后不再调用模型。"
                               % MAX_CALLS)

    game.calls += 1
    answer = model.chat(messages, json_mode=True, temperature=0.7, max_tokens=400,
                        source="stone", meta={"kb_ids": kb_ids})
    try:
        parsed = parse(answer["content"])
    except (ValueError, json.JSONDecodeError):
        # One repair attempt, at temperature 0, and both calls are in the log.
        repair = messages + [{"role": "assistant", "content": answer["content"]},
                             {"role": "user", "content": "That was not valid JSON. Reply with the "
                                                         "JSON object only."}]
        answer = model.chat(repair, json_mode=True, temperature=0.0, max_tokens=400,
                            source="stone-repair", meta={"kb_ids": kb_ids})
        parsed = parse(answer["content"])

    parsed["source"] = answer["model"]
    parsed["flags"] = []
    if HINDSIGHT.search(parsed["say"] + " " + parsed["zh"]):
        parsed["flags"].append("hindsight")
    parsed["usage"] = answer["usage"]
    parsed["cost"] = answer["cost"]
    parsed["seconds"] = answer["seconds"]
    parsed["at"] = answer["at"]
    usage = answer["usage"] or {}
    game.spend["calls"] += 1
    game.spend["in"] += int(usage.get("prompt_tokens") or 0)
    game.spend["out"] += int(usage.get("completion_tokens") or 0)
    game.spend["usd"] += float((answer["cost"] or {}).get("usd") or 0)
    _apply(game, parsed)
    return parsed


def _apply(game, parsed):
    """The world decides whether the proposed action can happen."""
    act = parsed["act"]
    before = len(game.shown)
    refusal = ""

    if act == "observe":
        game._say("世界", "Stone 举起望远镜，看了很久，没有说话。")
    elif act == "call_up":
        game._say("世界", "Stone 走到莫尔斯灯前，亲自打了一阵。没有回答。")
    elif act == "send_down":
        if game.sent_below:
            refusal = "他刚才已经叫你下去过一次了。"
        elif game.rockets < 3:
            refusal = "除了那盏灯，他还没有什么可报告的。"
        else:
            game.sent_below = True
            game.divergence = ("记录里，学徒是两点整被叫下去报告八枚火箭的；"
                               "这一局，Stone 提前叫了你下去。")
            game._say("世界", "Stone 忽然停下脚步：「下去见船长，叫醒他。"
                             "就说我们看见 %d 枚白色的火箭。」" % game.rockets,
                      zh="（记录没有这样写。他本来还要再看二十分钟。）")
    elif act == "nothing":
        if parsed["say"]:
            refusal = "他什么也没做，只是说了话。"
        else:
            game._say("世界", "Stone 没有回答。他望着那条船，手指在栏杆上敲了两下。")

    if parsed["say"]:
        game._say("Stone", parsed["say"], zh=parsed.get("zh") or parsed.get("say_zh"),
                  kind="stone")
    parsed["refusal"] = refusal
    game.stone = {"say": parsed["say"], "zh": parsed.get("zh") or parsed.get("say_zh"),
                  "act": act, "why": parsed.get("why", ""), "source": parsed["source"],
                  "flags": parsed["flags"], "refusal": refusal}


def _replay(utterance):
    """Offline: a reply recorded from a real call, and labelled as recorded."""
    if not FIXTURE_PATH.is_file():
        raise FixtureMiss("没有密钥，也没有录制好的回答。设置 DEEPSEEK_API_KEY 后再玩。")
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    key = " ".join(utterance.lower().split())
    for entry in fixture.get("replies", []):
        if " ".join(entry["utterance"].lower().split()) == key:
            reply = dict(entry["reply"])
            reply["source"] = "recorded fixture (not a live call)"
            reply["flags"] = list(reply.get("flags") or [])
            reply["cost"] = entry.get("cost")
            reply["usage"] = entry.get("usage")
            reply["seconds"] = 0
            reply["at"] = fixture.get("recorded_at")
            reply["fixture"] = True
            return reply
    raise FixtureMiss("这句没有录过。离线模式只重放录过的问答；点示例句，或设置密钥。")
