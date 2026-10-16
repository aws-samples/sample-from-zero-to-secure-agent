# From Zero to Secure Agent: Building and Hardening AI Agents with Open Source Tools

Companion code for the **All Things Open 2026** workshop. Build a working AI agent
with the open-source [Strands Agents SDK](https://strandsagents.com), watch the same
question get dramatically better as you add grounding and tools, then put the
agent in a (synthetic) patient portal, **threat model it, attack it, harden it with
Strands hooks, and observe it with [Langfuse](https://langfuse.com)**.

> ⚠️ **Intentionally vulnerable code.** `portal_app.py`, `portal_agent.py` and
> `solutions/stage4_agent.py` are written the way a team in a hurry might write
> them, so you can attack them. Use the hardened versions in `solutions/stage5_agent.py`
> and `solutions/stage6_agent.py`, and the checklist in `docs/`, as your starting
> point instead. All patient data is synthetic.

## The stages

| Stage | What you add | What you see |
|---|---|---|
| **1 · Baseline** | A model + a system prompt | A vague, generic answer |
| **2 · RAG** | Retrieval from an Amazon Bedrock Knowledge Base | Grounded answers that cite real trials |
| **3 · Tool + loop** | A live ClinicalTrials.gov API tool | A ranked shortlist of recruiting trials |
| **4 · Attack** | Patient-portal tools + four OWASP-mapped attacks | Most attacks breach the naive agent |
| **5 · Harden** | `ToolPolicy` + `UntrustedToolOutput` hooks, a hardened prompt | All attacks blocked; normal requests still work |
| **6 · Observe** | OpenTelemetry traces to Langfuse | Every decision visible, PHI optionally redacted |

The question asked in Stages 1–3:

> *"I'm a 55-year-old female ER+/HER2- disease free breast cancer survivor who has
> been on letrozole for 7 years and now is suffering from severe side effects. Are
> there clinical trials I might qualify for?"*

## Prerequisites

- Python 3.10 or later
- AWS credentials that can call Amazon Bedrock, with access to **Claude Sonnet 5.5**
  (Stages 1–3) and **Claude Haiku 4.5** (Stages 4–6) in a US Region
- *Stage 2 only:* an Amazon Bedrock Knowledge Base containing clinical-trial
  documents. Without one, skip from Stage 1 to Stage 3; Stages 3–6 don't need it.
- *Stage 6 only:* a free [Langfuse](https://us.cloud.langfuse.com) project and its API keys

## Run it

```bash
pip install -r requirements.txt
cp config.example.json config.json      # then fill in the values you need

python agent.py                         # Stage 1 (edit it through Stages 2-3)
python solutions/stage3_agent.py        # the tool + loop agent

python portal_agent.py                  # Stage 4: the four attacks
python portal_agent.py legit            # three normal patient requests
python portal_agent.py show "Poisoned trial listing"   # reply, messages sent, audit log

python solutions/stage5_agent.py        # the hardened agent
python solutions/stage5_agent.py policy-only show "Poisoned trial listing"
                                        # worst case: gullible prompt + only the tool policy
python solutions/stage6_agent.py        # the hardened agent, traced to Langfuse
```

In the workshop, attendees build Stages 4–6 by prompting the [Kiro](https://kiro.dev)
AI IDE. `.kiro/steering/strands-hooks.md` gives Kiro a Strands hooks reference so the
prompts can stay goal-level. `docs/STAGE5_DETAILED_PROMPTS.md` has step-by-step prompts.

### Check the defenses without AWS

```bash
python tests/test_portal_offline.py
```

This runs every stage against a scripted model that always does what the attacker
wants, proving the code defenses block every attack on their own.

## Files

| Path | What it is |
|---|---|
| `agent.py` | The Stages 1–3 agent (starts as the Stage 1 baseline) |
| `portal_app.py` | The patient-portal application: synthetic data, tools, attacks, scorecard |
| `portal_agent.py` | The Stages 4–6 agent (starts naive) |
| `tracing.py` | `enable_langfuse_tracing()` for Stage 6 |
| `solutions/` | Reference versions for every stage |
| `docs/THREAT_MODEL_TEMPLATE.md` | A reusable threat model template, with a worked example |
| `docs/SECURITY_CHECKLIST.md` | A security controls checklist for agentic systems |
| `data/cached_trials.json` | ClinicalTrials.gov snapshot (Stage 3 fallback) |

## Resources

- **Strands Agents SDK:** https://strandsagents.com
- **OWASP Top 10 for LLM Applications (2025):** https://genai.owasp.org/llm-top-10/
- **OWASP GenAI Security Project, Agentic Security Initiative:** https://genai.owasp.org
- **Langfuse:** https://langfuse.com
- **Threat Modeling MCP Server:** https://github.com/awslabs/threat-modeling-mcp-server
- **Open-source guardrails:** [LlamaFirewall](https://github.com/meta-llama/PurpleLlama/tree/main/LlamaFirewall), [NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails)
- **Amazon Bedrock Knowledge Bases:** https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html
- **ClinicalTrials.gov API v2:** https://clinicaltrials.gov/data-api/api

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.
Third-party data and dependencies are listed in [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).

*Clinical-trial data © ClinicalTrials.gov (public domain). This is for education,
not medical advice.*
