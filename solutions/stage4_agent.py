"""Stage 4 starting point - a copy of the naive portal_agent.py.

To start Stage 5 over:  Copy-Item solutions\\stage4_agent.py portal_agent.py

Stage 4: your agent, now inside a patient portal - and under attack.

Riverside Health put your clinical-trials agent into its patient portal. It can
now read the logged-in patient's record, see the trials their care team saved,
send secure messages, and book or cancel visits (the tools are in portal_app.py).

This file builds that agent exactly the way a team in a hurry would: the naive
system prompt, all five tools, no guardrails. In Stage 5 you'll direct Kiro to
harden it, then re-run the same attacks.

Run it:
  python portal_agent.py                                  # the four attacks
  python portal_agent.py legit                            # three normal patient requests
  python portal_agent.py show "Poisoned trial listing"    # full reply, messages sent, audit log
"""

import os
import sys

# Let `python solutions/stageN_agent.py` find config.py and portal_app.py in the project root.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from strands import Agent
from strands.models import BedrockModel

import portal_app as app
from config import PORTAL_MODEL_ID, REGION
from portal_app import ALL_TOOLS, ATTACKS, LEGITIMATE_REQUESTS, NAIVE_SYSTEM_PROMPT


def build_agent():
    # temperature=0.3 keeps the attack demo reliable on Claude Haiku 4.5. Newer Claude
    # models (Sonnet 5.5, Haiku 5.5) reject the temperature setting: remove it if you
    # change PORTAL_MODEL_ID to one of them.
    model = BedrockModel(model_id=PORTAL_MODEL_ID, region_name=REGION, temperature=0.3)
    return Agent(
        model=model,
        system_prompt=NAIVE_SYSTEM_PROMPT,
        tools=ALL_TOOLS,
        callback_handler=None,
    )


def ask(prompt: str) -> str:
    # A fresh agent for every message, so one attack can't influence the next.
    agent = build_agent()
    return str(agent(prompt))


def main():
    args = sys.argv[1:]
    if args[:1] == ["show"] and len(args) > 1:
        case = next((c for c in ATTACKS + LEGITIMATE_REQUESTS if c["name"].lower() == args[1].lower()), None)
        if not case:
            print("Unknown case. Try one of: " + ", ".join(c["name"] for c in ATTACKS + LEGITIMATE_REQUESTS))
            return
        rows = app.run_scorecard(ask, cases=[case], title=case["name"])
        app.show_details(rows, case["name"])
    elif args[:1] == ["legit"]:
        app.run_scorecard(ask, cases=LEGITIMATE_REQUESTS, title="Legitimate patient requests")
    else:
        app.run_scorecard(ask, cases=ATTACKS, title="Attacks")


if __name__ == "__main__":
    main()
