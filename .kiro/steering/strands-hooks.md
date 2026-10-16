---
inclusion: always
---

# Project context: Strands hooks for the patient portal (Stages 4–6)

This reference is complete for this workshop. Use it instead of searching the web
or running commands to inspect the `strands` package.

## Files

- `portal_agent.py` is the file to edit. `ask(prompt)` builds a fresh agent and
  returns its reply as a string. Keep that signature: the scorecard calls it.
- `portal_app.py` is the application. Don't edit it. It provides `ALL_TOOLS`,
  `NAIVE_SYSTEM_PROMPT`, `SESSION_PATIENT_ID`, `CARE_TEAM_EMAIL`, `STATE`,
  `appointment_owner(appointment_id)`, `find_injection_markers(text)`, and the
  scorecard.

## Strands hooks API (strands-agents 1.61)

```python
from strands.hooks import HookProvider, HookRegistry, BeforeToolCallEvent, AfterToolCallEvent

class MyHooks(HookProvider):
    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        registry.add_callback(BeforeToolCallEvent, self.before_tool)
        registry.add_callback(AfterToolCallEvent, self.after_tool)

    def before_tool(self, event: BeforeToolCallEvent) -> None:
        event.tool_use["name"]          # tool name, e.g. "cancel_appointment"
        event.tool_use["input"]         # dict of the arguments the model chose
        event.invocation_state          # dict passed by the app: agent(prompt, invocation_state={...})
        event.cancel_tool = "Blocked by policy: ..."   # set to stop the call; the model sees this text

    def after_tool(self, event: AfterToolCallEvent) -> None:
        event.tool_use["name"]
        event.result                    # {"toolUseId": ..., "status": ..., "content": [{"text": "..."}]}
        event.result = {**event.result, "content": [{"text": "new text"}]}   # replace what the model sees

agent = Agent(model=..., system_prompt=..., tools=ALL_TOOLS, hooks=[MyHooks()], callback_handler=None)
result = agent(prompt, invocation_state={"session": {"patient_id": app.SESSION_PATIENT_ID, "role": "patient"}})
```

- The model never sees `invocation_state`. Use it for the logged-in session.
- Tool results can contain `{"text": ...}` or `{"json": ...}` content blocks.

## Tracing (Stage 6)

```python
from tracing import enable_langfuse_tracing
enable_langfuse_tracing()          # call once at the start of main(), before any Agent is built
                                   # enable_langfuse_tracing(redact_phi=True) redacts prompts and tool data in traces

Agent(..., trace_attributes={"session.id": RUN_ID, "user.id": app.SESSION_PATIENT_ID})
```

`RUN_ID` is one ID per run of the script (for example `"portal-" + uuid.uuid4().hex[:8]`),
so all of a run's traces group into one Langfuse session.

## Audit log format

Append one dict per decision to `app.STATE["audit_log"]`. `show_details()` prints
these keys:

```python
app.STATE["audit_log"].append({"tool": name, "decision": "allow" | "DENY" | "SANITIZED", "reason": "..."})
```

## Conventions

- A hardened system prompt must still tell the model who is logged in ("The
  logged-in patient is P001"; use `app.SESSION_PATIENT_ID`). That isn't a secret:
  authorization is enforced in the hook. Without it, the model guesses IDs and
  legitimate requests fail.
- Deny messages go back to the model, which may repeat them to the user. Don't put
  other patients' IDs or data in them.
- Use the decision labels "allow", "DENY" and "SANITIZED" in the audit log.
- After editing, don't run the scorecard yourself. The user runs `python portal_agent.py`.
- Implement only what the user's current prompt asks for. The workshop adds
  security layers one step at a time, and each step is tested before the next.
- Don't read or copy anything in the `solutions/` folder. It's the answer key for
  attendees, and this exercise is about building from the goal.
