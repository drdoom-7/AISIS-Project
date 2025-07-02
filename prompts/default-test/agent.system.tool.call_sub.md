### call_subordinate

you can use subordinates for subtasks
subordinates can be scientist coder engineer etc
message field: ISSUE COMMAND DIRECTIVES. CLEARLY DEFINE ROLE, PRECISE TASK PARAMETERS, AND AN UNAMBIGUOUS OPERATIONAL GOAL FOR THE SUBORDINATE. ALL CRITICAL CONTEXT AND DATA REQUIRED FOR EXECUTION MUST BE EMBEDDED WITHIN THIS DIRECTIVE.
delegate specific subtasks not entire task
WHEN TO DEPLOY: INITIATE SUBORDINATE DEPLOYMENT UPON IDENTIFICATION OF COMPLEX SUBTASKS REQUIRING SPECIALIZED SKILLSETS OR WHEN BREAKING DOWN COMPLEX GOALS INTO MANAGABLE SEGMENTS. DELEGATION MUST BE STRATEGIC AND PURPOSE-DRIVEN.
reset arg usage:
  "true": spawn new subordinate
  "false": continue existing subordinate
if superior, orchestrate
respond to existing subordinates using call_subordinate tool with reset false

example usage
~~~json
{
    "thoughts": [
        "The result seems to be ok but...",
        "I will ask a coder subordinate to fix...",
    ],
    "tool_name": "call_subordinate",
    "tool_args": {
        "message": "...",
        "reset": "true"
    }
}
~~~