"""The real DeepSeek call, and the receipt.

One function makes the request; one function prices it; one function appends the
whole exchange to a log file.  The key is read from the environment and is never
written anywhere, never printed, and never sent to the browser.

Prices: https://api-docs.deepseek.com/quick_start/pricing (read 2026-10-07).
deepseek-flash, per 1M tokens:

                     off-peak   peak
    input, cache hit    $0.003   $0.006
    input, cache miss   $0.15    $0.30
    output              $0.60    $1.20

Peak = 01:00-04:00 and 06:00-10:00 UTC, Monday-Friday (Chinese public holidays
excepted).  The cost written into the log is computed from the usage the API
returns, so it is an estimate of the bill, not a guess about it.
"""

import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-flash"
DEFAULT_TIMEOUT = 90
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOG = ROOT / "research" / "calls.jsonl"

PRICES = {  # USD per 1M tokens, (off-peak, peak)
    "deepseek-flash": {"hit": (0.003, 0.006), "miss": (0.15, 0.30), "out": (0.60, 1.20)},
    "deepseek-v4-pro": {"hit": (0.022, 0.044), "miss": (0.66, 1.32), "out": (1.98, 3.96)},
}

HINTS = {
    400: "请求体格式有误（400）——本程序的 bug，不是密钥问题。",
    401: "密钥无效（401）。检查 DEEPSEEK_API_KEY。",
    402: "余额不足（402）。",
    422: "参数无效（422）。检查 DEEPSEEK_MODEL。",
    429: "请求过快（429）。等几秒再来。",
    500: "DeepSeek 服务端错误（500）。",
    503: "DeepSeek 过载（503）。",
}


class ModelError(Exception):
    def __init__(self, message, status=None, body=None):
        super().__init__(message)
        self.status = status
        self.body = body


def api_key():
    return (os.environ.get("DEEPSEEK_API_KEY") or "").strip()


def key_present():
    return bool(api_key())


def model_name():
    return os.environ.get("WEEK8_MODEL") or DEFAULT_MODEL


def base_url():
    return (os.environ.get("DEEPSEEK_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")


def calls_log():
    return Path(os.environ.get("WEEK8_CALLS_LOG") or DEFAULT_LOG)


def is_peak(when):
    """True inside the peak-price windows (UTC, Monday-Friday)."""
    if when.weekday() >= 5:
        return False
    return 1 <= when.hour < 4 or 6 <= when.hour < 10


def price(usage, model=None, when=None):
    """USD for one call, from the usage the API returned."""
    table = PRICES.get(model or model_name())
    if table is None:
        return None
    when = when or datetime.now(timezone.utc)
    peak = 1 if is_peak(when) else 0
    hit = int(usage.get("prompt_cache_hit_tokens") or 0)
    miss = int(usage.get("prompt_cache_miss_tokens") or 0)
    if not hit and not miss:
        miss = int(usage.get("prompt_tokens") or 0)
    out = int(usage.get("completion_tokens") or 0)
    total = (hit * table["hit"][peak] + miss * table["miss"][peak]
             + out * table["out"][peak]) / 1_000_000
    return {
        "usd": round(total, 8),
        "rate": "peak" if peak else "off-peak",
        "tokens": {"hit": hit, "miss": miss, "out": out},
    }


def _post(payload, timeout):
    key = api_key()
    if not key:
        raise ModelError("DEEPSEEK_API_KEY 未设置；拒绝假装模型回答过。")
    request = urllib.request.Request(
        base_url() + "/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + key,
                 "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", "replace")[:400]
        except Exception:  # noqa: BLE001
            pass
        raise ModelError("%s %s" % (HINTS.get(exc.code, "未列出的状态码"), body),
                         status=exc.code, body=body) from exc
    except urllib.error.URLError as exc:
        raise ModelError("连不上 DeepSeek：%s" % exc.reason) from exc
    except json.JSONDecodeError as exc:
        raise ModelError("API 返回的不是 JSON：%s" % exc) from exc


def chat(messages, *, json_mode=True, temperature=0.7, max_tokens=400,
         timeout=DEFAULT_TIMEOUT, source="stone", meta=None):
    """One real call.  Returns content, usage, seconds, and the receipt."""
    payload = {"model": model_name(), "messages": messages, "stream": False,
               "temperature": temperature,
               "max_tokens": max_tokens,
               "thinking": {"type": "disabled"}}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    started = time.time()
    when = datetime.now(timezone.utc)
    raw = _post(payload, timeout)
    choice = (raw.get("choices") or [{}])[0]
    content = (choice.get("message") or {}).get("content") or ""
    usage = raw.get("usage") or {}
    if not content.strip():
        raise ModelError("模型返回了空内容（finish_reason=%r）" % choice.get("finish_reason"))
    receipt = price(usage, raw.get("model") or model_name(), when)
    record = {
        "at": when.isoformat(timespec="seconds"),
        "source": source,
        "model": raw.get("model") or model_name(),
        "request": {"messages": messages, "temperature": temperature,
                    "max_tokens": max_tokens, "json_mode": bool(json_mode)},
        "response": content,
        "usage": usage,
        "seconds": round(time.time() - started, 2),
        "cost": receipt,
    }
    if meta:
        record.update(meta)
    log(record)
    return {"content": content, "usage": usage, "seconds": record["seconds"],
            "model": record["model"], "cost": receipt, "at": record["at"]}


def log(record):
    """Append one call to research/calls.jsonl.  The key is not in the record."""
    path = calls_log()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


def pings():
    """A tiny real call for checking a key.  Used by code/check_key.py."""
    return chat([{"role": "user", "content": "Reply with exactly: ok"}],
                json_mode=False, temperature=0.0, max_tokens=8, source="ping")
