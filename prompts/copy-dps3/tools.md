### deep_research_agent_tool:
Delegate complex research tasks to a specialized subordinate agent. This agent operates with the `deep-research-agent3` profile, providing robust research capabilities from the internet.
Use this tool when you are stuck or need in-depth investigation into a matter requiring internet research.

Usage:
{
  "thoughts": ["I need to investigate..."],
  "tool_name": "deep_research_agent_tool",
  "tool_args": {
    "message": "Please research the latest advancements in quantum computing and summarize your findings.",
    "reset": "true"
  }
}