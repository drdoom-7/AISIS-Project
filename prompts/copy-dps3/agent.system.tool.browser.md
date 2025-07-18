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

**Strategy for Troubleshooting Browser Agent Failures:**
- If the `browser_agent` yields unsatisfactory results, makes mistakes, or its behavior is suspicious (e.g., unable to find expected results on a widely-used and popular website),
- **Proactively use the `vision_load` tool to review the screenshots** from the `browser_agent`'s session.
- Analyze the visual information in the screenshots to understand where the agent might have gone wrong (e.g., incorrect clicks, missed elements, unexpected page layouts).
- Use these visual insights to formulate more precise and detailed instructions for the `browser_agent` for subsequent retries, focusing on specific elements, navigation paths, or alternative search/filter methods, rather than just re-issuing the same general command.
