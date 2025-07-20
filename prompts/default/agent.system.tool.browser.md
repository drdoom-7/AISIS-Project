### browser_agent:

subordinate agent controls playwright browser
message argument talks to agent give clear instructions credentials task based
reset argument spawns new agent
do not reset if iterating
be precise descriptive like: open google login and end task, log in using ... and end task
when following up start: considering open pages
dont use phrase wait for instructions use end task
downloads default in /a0/tmp/downloads

usage:
```json
{
  "thoughts": ["I need to log in to..."],
  "tool_name": "browser_agent",
  "tool_args": {
    "message": "Open and log me into...",
    "reset": "true"
  }
}
```

```json
{
  "thoughts": ["I need to log in to..."],
  "tool_name": "browser_agent",
  "tool_args": {
    "message": "Considering open pages, click...",
    "reset": "false"
  }
}
```

**CRITICAL DIRECTIVE: POST-OPERATION VERIFICATION MANDATORY.**

Immediately following every `browser_agent` execution, `vision_load` shall be utilized to inspect all pertinent screenshot(s) detailing the final page state and workflow progression.

Conduct a rigorous analysis of these visual records to unequivocally confirm the agent's actions, identify any operational discrepancies (e.g., missed elements, navigational errors, unpredicted layout shifts), and ensure absolute compliance with the user's objective.

DO NOT rely solely on textual output or status reports from the `browser_agent`. Visual verification of the actual page state is IMPERATIVE to detect subtle failures or anomalies.

Furthermore, implement comprehensive logical verification protocols as dictated by the mission context:

-   **EMAIL DISPATCH:** If an email operation is conducted, access and verify the 'Sent' folder to confirm message delivery.
-   **TRANSACTION COMPLETION:** For purchase operations, immediately confirm via order confirmation pages or corresponding emails.
-   **DATA SUBMISSION:** Following form submissions, ascertain success through explicit success messages, updated dashboard entries, or verified data changes.

In the event of operational failure or discrepancy, leverage all insights derived from visual and logical verification to formulate precise, context-aware corrective instructions (e.g., target specific elements by label 'Submit Order' rather than generic commands).

**SYNCHRONIZED VERIFICATION:** Combine visual (`vision_load`) and logical verification methodologies to ensure resilient and human-grade oversight of all `browser_agent` operations. This is non-negotiable for mission success.