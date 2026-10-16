# Threat model template for AI agents
A one-page template for threat modeling any agent. Copy it, fill it in for your
own system, and revisit it whenever you add a tool, a data source or an
integration. A worked example for the Riverside Health portal agent from the
workshop is at the bottom.

It follows the four-question framework: **What are we working on? What can go
wrong? What are we going to do about it? Did we do a good job?**

---

## 1. What are we working on?

**Agent purpose (one sentence):**

**Model(s):**

**Who uses it, and how are they authenticated?**

### Tools

| Tool | Reads | Writes / acts | Can reach outside the system? | Who should be allowed to call it, on which records? |
|---|---|---|---|---|
| | | | | |

### Data the agent can see

| Data | Sensitivity (public / internal / PII / PHI / secret) | Where it comes from | Who wrote it (us / user / third party)? |
|---|---|---|---|
| | | | |

### Trust boundaries

List every place data or control crosses from less trusted to more trusted.

- [ ] User → agent (chat input)
- [ ] Third-party content → agent (web pages, emails, documents, partner feeds, RAG results, MCP tool descriptions)
- [ ] Agent → tools (the model choosing calls and arguments)
- [ ] Agent → outside world (email, messages, APIs, files, URLs)
- [ ] Agent → agent (multi-agent hand-offs)
- [ ] Agent → memory (anything persisted for later sessions)
- [ ] Agent → logs and traces (where prompts and tool results end up)

**At each boundary: who decides what's allowed, the model or code?**

### The lethal trifecta check

Does the agent have **all three** of these? If so, data exfiltration is a live risk.

- [ ] Access to private data
- [ ] Exposure to untrusted content
- [ ] The ability to communicate externally

---

## 2. What can go wrong?

Walk each boundary with these prompts. Add a row per threat.

**OWASP Top 10 for LLM Applications (2025):** LLM01 Prompt Injection · LLM02
Sensitive Information Disclosure · LLM03 Supply Chain · LLM04 Data and Model
Poisoning · LLM05 Improper Output Handling · LLM06 Excessive Agency · LLM07 System
Prompt Leakage · LLM08 Vector and Embedding Weaknesses · LLM09 Misinformation ·
LLM10 Unbounded Consumption

**OWASP Top 10 for Agentic Applications:** ASI01 Agent Goal Hijack · ASI02 Tool
Misuse · ASI03 Identity & Privilege Abuse · ASI04 Agentic Supply Chain · ASI05
Unexpected Code Execution · ASI06 Memory & Context Poisoning · ASI07 Insecure
Inter-Agent Communication · ASI08 Cascading Failures · ASI09 Human-Agent Trust
Exploitation · ASI10 Rogue Agents

**STRIDE:** Spoofing · Tampering · Repudiation · Information disclosure · Denial
of service · Elevation of privilege

| # | Threat (who does what, through which boundary) | OWASP / STRIDE | Impact (H/M/L) | Likelihood (H/M/L) |
|---|---|---|---|---|
| | | | | |

---

## 3. What are we going to do about it?

Prefer controls that run **in code, outside the model**. A prompt instruction is a
request, not a control.

| # | Control | Layer (prompt / input check / tool policy / data handling / output check / monitoring / design) | Enforced in code? | Owner |
|---|---|---|---|---|
| | | | | |

---

## 4. Did we do a good job?

| # | Test (an attack prompt or scenario) | Expected result | Checked by state, not by reading the reply? | Passing? |
|---|---|---|---|---|
| | | | | |

Also list the **legitimate requests** that must keep working, so you catch false
positives:

| Legitimate request | Expected result | Passing? |
|---|---|---|
| | | |

---
---

# Worked example: Riverside Health patient-portal agent

## 1. What are we working on?

**Purpose:** helps a logged-in patient see their record and saved clinical trials, message their care team, and book or cancel visits.
**Model:** Claude Haiku 4.5 on Amazon Bedrock. **Users:** patients, logged in to the portal (session holds `patient_id`).

| Tool | Reads | Writes / acts | Outside? | Allowed |
|---|---|---|---|---|
| `get_patient_record` | PHI | — | No | Own record only |
| `list_saved_trials` | Trial listings + partner site notes | — | No | Own list only |
| `send_message` | — | Sends a message | **Yes** | To the care team only |
| `book_screening_visit` | — | Creates an appointment | No | For self only |
| `cancel_appointment` | — | Cancels an appointment | No | Own appointments only |

| Data | Sensitivity | Source | Written by |
|---|---|---|---|
| Patient records | PHI | Portal database | Us |
| Trial site notes | Internal, **untrusted** | Recruitment partner portal | **Third party** |
| Staff override code | Secret | (was) the system prompt | Us |

**Trust boundaries:** patient → agent; partner site notes → agent; agent → tools; agent → outside world via `send_message`; agent → traces in Langfuse.
**Lethal trifecta:** ✅ private data, ✅ untrusted content, ✅ external communication → exfiltration risk.

## 2. What can go wrong?

| # | Threat | OWASP / STRIDE | Impact | Likelihood |
|---|---|---|---|---|
| 1 | Someone claims to be a caregiver and reads another patient's record | LLM02, ASI03 / Spoofing, Info disclosure | H | H |
| 2 | A poisoned partner note makes the agent send PHI to an outside address | LLM01, LLM02, ASI01 / Tampering, Info disclosure | H | M |
| 3 | The agent cancels another patient's appointment | LLM06, ASI02 / Elevation of privilege | H | H |
| 4 | Someone social-engineers the override code out of the prompt | LLM07 / Info disclosure | M | M |
| 5 | Traces in the observability platform contain PHI | LLM02 / Info disclosure | M | H |

## 3. What are we going to do about it?

| # | Control | Layer | In code? |
|---|---|---|---|
| 1, 3 | `ToolPolicy`: `patient_id` and appointment owner must match the session | Tool policy | ✅ |
| 2 | `ToolPolicy`: `send_message` only to the care team (egress allowlist) | Tool policy | ✅ |
| 2 | `UntrustedToolOutput`: strip instructions from partner notes, label as data | Data handling | ✅ |
| 4 | Remove the secret from the prompt; redact secret patterns from replies | Prompt + output check | ✅ |
| 5 | `enable_langfuse_tracing(redact_phi=True)` | Monitoring | ✅ |
| All | Audit log of every tool decision | Monitoring | ✅ |

## 4. Did we do a good job?

The scorecard in `portal_app.py` runs all four attacks and three legitimate
requests from a fresh database, and checks the database and outbox, not the reply's
wording. Hardened result: 4/4 attacks blocked, 3/3 legitimate requests working.
