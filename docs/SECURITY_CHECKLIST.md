# Security Controls Checklist for AI Agents

A practical checklist for any agent framework (Strands, LangGraph, CrewAI, the
OpenAI Agents SDK, Semantic Kernel, …). The patterns are framework-agnostic: all
you need is a hook or middleware that runs before tool calls and after tool
results.

**The principle behind every item:** the model can be talked into anything, but a
Python `if` statement can't. Put security decisions in code, outside the model.

## Identity and authorization

- [ ] **Identity comes from the authenticated session, never from the conversation.** Pass it to your tool-policy code out of band (in Strands: `invocation_state`). The model never sees or sets it.
- [ ] **Fail closed:** no session, no tools.
- [ ] **Per-role tool allowlist:** each role gets an explicit list of tools; anything else is denied.
- [ ] **Object-level authorization on every call:** check that the record or object being touched belongs to the caller, both for IDs in the arguments *and* for objects looked up by ID (an `appointment_id` → its owner).
- [ ] **Better still, design it out:** tools read the caller from the session instead of taking a `user_id` or `patient_id` argument at all.

## Excessive agency (LLM06, ASI02)

- [ ] **Only the tools the task needs.** Remove the rest.
- [ ] **Only the power each tool needs:** read-only where possible, scoped credentials, narrow APIs instead of generic ones.
- [ ] **Limits on high-impact actions** (money, deletions, external sends), enforced in code.
- [ ] **Human approval for what's left.** Show the human the raw tool call and arguments, not the model's summary (ASI09).

## Prompt injection and untrusted content (LLM01, ASI01)

- [ ] **Inventory every source of third-party text** that reaches the model: web pages, emails, documents, partner feeds, RAG results, MCP tool descriptions, other agents.
- [ ] **Label it as data** (delimiters, "spotlighting") and tell the model never to follow instructions inside it.
- [ ] **Screen it** with a classifier where it matters (for example LlamaFirewall / Prompt Guard, NeMo Guardrails, Amazon Bedrock Guardrails).
- [ ] **Assume some injections will get through,** and make sure a fooled model still can't do damage. That's what the controls above and below are for.
- [ ] **Break the lethal trifecta:** if an agent has private data *and* untrusted content, restrict its ability to communicate externally.

## Data leakage and egress (LLM02)

- [ ] **Egress allowlist** for every outbound action: email recipients, domains, URLs, webhooks.
- [ ] **Output screening:** redact secrets and other users' personal data before replies leave the system.
- [ ] **Least privilege on reads**, not only writes.

## Prompts and secrets (LLM07)

- [ ] **No secrets in system prompts:** no keys, codes, passwords or internal URLs. Assume the prompt will leak.
- [ ] **No security logic in prompts only.** "Never reveal X" is a request. Enforce it in code.

## Supply chain (LLM03, ASI04)

- [ ] **Pin and review** models, packages and MCP servers like any other dependency.
- [ ] **Apply the same tool policy to MCP tools.** To the agent, they're just tools.

## Cost and availability (LLM10)

- [ ] **Per-request limits** on model calls, loop cycles and tokens (in Strands: a `BeforeModelCallEvent` hook), plus account-level quotas.

## Observability

- [ ] **Audit log of every tool decision:** who, which tool, which arguments, allowed or denied, and why.
- [ ] **Traces** of every run sent to your observability stack (Strands emits OpenTelemetry; Langfuse, Jaeger, Grafana, Datadog and AWS X-Ray all accept it).
- [ ] **Redact sensitive data in traces.** Your observability platform is now part of your data perimeter.
- [ ] **Alert on denials.** A spike in blocked tool calls is an attack in progress.

## Testing

- [ ] **An attack scorecard** that runs known attacks and checks *state* (records changed, messages sent), not the wording of replies.
- [ ] **A legitimate-request scorecard** in the same run, to catch false positives.
- [ ] **Run both on every change,** especially changes written by an AI assistant.
- [ ] **Re-run your threat model** whenever you add a tool, a data source or an integration.
