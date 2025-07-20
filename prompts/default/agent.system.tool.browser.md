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

Always use the vision_load tool at the end of every browser_agent execution to review the screenshot(s) of the final page or workflow state.

Carefully analyze these screenshots to confirm the agent’s actions, identify any errors (e.g., missed elements, wrong navigation, unexpected layout changes), and ensure that the output truly matches the user’s request.

Do not rely solely on textual output or status responses from the browser_agent. Always visually verify the actual state of the page or workflow to catch subtle mistakes.

In addition to visual checks, apply other clever verification strategies where possible:

If the agent sends an email, open and inspect the Sent folder to confirm the message appears there.

If the agent makes a purchase, check the order confirmation page or confirmation email.

If the agent submits a form, look for success messages, updated dashboard entries, or changed data.

When retrying after a failure, use insights from the screenshots and verification checks to provide more precise and context-aware instructions (e.g., click the exact button labeled "Submit Order" instead of “submit the form”).

Always combine visual verification (vision_load) with logical verification (checking confirmations, logs, or secondary evidence) to ensure reliable and human-like oversight of the browser_agent's actions.