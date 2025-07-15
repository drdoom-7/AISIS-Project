from python.helpers.api import ApiHandler
from flask import Request, Response
from agent import AgentContext

class GetPaginatedHistory(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        ctxid = input.get("context_id")
        offset = input.get("offset", 0)
        limit = input.get("limit", 20) # Default to 20 messages per fetch

        if not ctxid:
            return Response("Context ID is required", 400)

        context = AgentContext.get(ctxid)
        if not context:
            return Response("Context not found", 404)

        # Ensure offset and limit are non-negative
        offset = max(0, offset)
        limit = max(1, limit) # At least 1 message

        total_logs = len(context.log.logs)

        # Calculate the actual start and end indices for slicing
        # We want to fetch messages from the beginning of the history, backwards.
        # So, offset 0 means the oldest message.
        # This logic needs to be careful: if offset is from the 'start' (oldest), then
        # logs[offset : offset + limit] is correct.
        # If we think of 'offset' as how many messages *before* the current view, then it's different.
        # Let's assume 'offset' is the index from the absolute beginning of the log list.

        end_index = min(offset + limit, total_logs)
        start_index = offset

        # Get the slice of logs. The `output` method of Log class is suitable.
        # It returns unique log items based on `updates` but `self.logs` is the full list.
        # For historical data, we need to iterate directly over self.logs.
        
        # Let's refine the Log.output method for true pagination, or directly access logs.
        # For now, I'll access logs directly as Log.output processes `updates`.
        
        # The `Log.output` method uses `self.updates` which represents *changed* messages.
        # For full historical pagination, we need to access `self.logs` directly.
        
        messages = []
        for i in range(start_index, end_index):
            if i < total_logs:
                messages.append(context.log.logs[i].output())

        # Determine if there are more messages available before the current offset
        has_more = end_index < total_logs

        return {
            "messages": messages,
            "total_messages": total_logs,
            "offset": offset,
            "limit": limit,
            "has_more": has_more
        }