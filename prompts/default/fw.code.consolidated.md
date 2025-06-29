# Framework Code Execution Messages

This file consolidates various system messages related to the `code_execution_tool`.

## Information Messages
### Code Execution Info
[SYSTEM: {{info}}]

## Timeout and Progress Messages
### Max Execution Time Reached
Returning control to agent after {{timeout}} seconds of execution. Process is still running. Decide whether to wait for more output or reset based on context.

### No Output After Timeout
Returning control to agent after {{timeout}} seconds with no output. Process is still running. Decide whether to wait for more output or reset based on context.

### Pause Time Since Last Output
Returning control to agent after {{timeout}} seconds since last output update. Process is still running. Decide whether to wait for more output or reset based on context.

## No Output/Completion Messages
### No Output Returned
No output returned. Consider resetting the terminal or using another session.

### Terminal Session Reset
Terminal session has been reset.

## Error Messages
### Unsupported Runtime
```json
{
    "system_warning": "The runtime '{{runtime}}' is not supported, available options are 'terminal', 'python', 'nodejs' and 'output'."
}
```