"""
Token logger for unslop crew. Tracks tokens from two call paths:

1. CrewAI native providers (AnthropicCompletion etc.) — hooks into
   BaseLLM._track_token_usage_internal, called after every native provider call.

2. Direct litellm calls — wraps litellm.completion and litellm.acompletion.

Why two paths: CrewAI routes Anthropic models through its own native SDK provider
that bypasses litellm entirely. litellm's internal callback APIs also have gaps
(sync path only fires if customLogger was previously initialized).

Persists to outputs/token_log.jsonl. Budget: $100 total.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import litellm
import story_context

import config

LOG_PATH = config.OUTPUTS / "token_log.jsonl"
BUDGET = 225.00

# Per-token costs (USD) — strip provider prefix before lookup
COSTS = {
    "claude-haiku-4-5-20251001": {"input": 1e-6,   "output": 5e-6},
    "claude-sonnet-4-6":         {"input": 3e-6,   "output": 1.5e-5},
    "claude-opus-4-7":           {"input": 15e-6,  "output": 75e-6},
    "claude-opus-4-5":           {"input": 15e-6,  "output": 75e-6},
}


def _write_tokens(model: str, input_tokens: int, output_tokens: int) -> None:
    model_key = model.split("/")[-1] if "/" in model else model
    rates = COSTS.get(model_key, {"input": 0, "output": 0})
    cost  = (input_tokens * rates["input"]) + (output_tokens * rates["output"])

    record = {
        "ts":    datetime.now(timezone.utc).isoformat(),
        "model": model_key,
        "slug":  story_context.get_story() or "",
        "in":    input_tokens,
        "out":   output_tokens,
        "cost":  round(cost, 6),
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")

    total = _total_spend()
    if total >= BUDGET:
        raise RuntimeError(f"Budget exhausted: ${total:.4f} >= ${BUDGET:.2f}. Halt.")


def _write_from_litellm_usage(model: str, usage) -> None:
    """For litellm response usage objects (prompt_tokens / completion_tokens)."""
    if usage is None:
        return
    _write_tokens(
        model,
        getattr(usage, "prompt_tokens",     0) or 0,
        getattr(usage, "completion_tokens", 0) or 0,
    )


def _write_from_usage_dict(model: str, usage_data: dict) -> None:
    """For CrewAI native provider usage dicts (input_tokens / output_tokens)."""
    if not usage_data:
        return
    in_tok  = usage_data.get("prompt_tokens")     or usage_data.get("input_tokens")  or 0
    out_tok = usage_data.get("completion_tokens") or usage_data.get("output_tokens") or 0
    if in_tok == 0 and out_tok == 0:
        return
    _write_tokens(model, in_tok, out_tok)


# ── litellm path ──────────────────────────────────────────────────────────────

_original_completion  = litellm.completion
_original_acompletion = litellm.acompletion


def _patched_completion(*args, **kwargs):
    result = _original_completion(*args, **kwargs)
    _write_from_litellm_usage(kwargs.get("model", "unknown"), getattr(result, "usage", None))
    return result


async def _patched_acompletion(*args, **kwargs):
    result = await _original_acompletion(*args, **kwargs)
    _write_from_litellm_usage(kwargs.get("model", "unknown"), getattr(result, "usage", None))
    return result


litellm.completion  = _patched_completion
litellm.acompletion = _patched_acompletion

# ── CrewAI native provider path ───────────────────────────────────────────────

try:
    from crewai.llms.base_llm import BaseLLM as _BaseLLM

    _original_track = _BaseLLM._track_token_usage_internal

    def _patched_track(self, usage_data: dict) -> None:
        _write_from_usage_dict(getattr(self, "model", "unknown"), usage_data)
        return _original_track(self, usage_data)

    _BaseLLM._track_token_usage_internal = _patched_track

except ImportError:
    pass  # crewai not installed — litellm path still active

# ── litellm settings ──────────────────────────────────────────────────────────

litellm.num_retries = 3
litellm.request_timeout = 120  # seconds — long enough for large vision payloads


# ── reporting ─────────────────────────────────────────────────────────────────

def _load_records():
    if not LOG_PATH.exists():
        return []
    with open(LOG_PATH) as f:
        return [json.loads(line) for line in f if line.strip()]


def _total_spend():
    return sum(r["cost"] for r in _load_records())


def report():
    records = _load_records()
    if not records:
        print("No calls logged yet.")
        return

    by_model = {}
    for r in records:
        m = r["model"]
        if m not in by_model:
            by_model[m] = {"calls": 0, "in": 0, "out": 0, "cost": 0.0}
        by_model[m]["calls"] += 1
        by_model[m]["in"]    += r["in"]
        by_model[m]["out"]   += r["out"]
        by_model[m]["cost"]  += r["cost"]

    total     = sum(v["cost"] for v in by_model.values())
    remaining = BUDGET - total

    print(f"\n{'Model':<35} {'Calls':>6} {'In tok':>10} {'Out tok':>10} {'Cost':>10}")
    print("-" * 75)
    for model, v in sorted(by_model.items()):
        print(f"{model:<35} {v['calls']:>6} {v['in']:>10,} {v['out']:>10,} ${v['cost']:>9.4f}")
    print("-" * 75)
    total_calls = sum(v["calls"] for v in by_model.values())
    print(f"{'TOTAL':<35} {total_calls:>6} {'':>21} ${total:>9.4f}")
    print(f"\nBudget: ${BUDGET:.2f}   Spent: ${total:.4f}   Remaining: ${remaining:.4f}")
    if remaining < 10:
        print("WARNING: less than $10 remaining.")


def check_budget():
    """Raise if total spend is at or above budget. Returns current spend."""
    total = _total_spend()
    if total >= BUDGET:
        raise RuntimeError(f"Budget exhausted: ${total:.4f} of ${BUDGET:.2f} spent.")
    return total
