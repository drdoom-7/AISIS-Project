import asyncio
from python.helpers.extension import Extension
from agent import Agent
from python.helpers.memory import Memory
from agent import LoopData

DATA_NAME_TASK = "_recall_memories_task"

class RecallMemories(Extension):

    INTERVAL = 3
    HISTORY = 10000
    RESULTS = 3
    THRESHOLD = 0.6

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):

        # every 3 iterations (or the first one) recall memories
        if loop_data.iteration % RecallMemories.INTERVAL == 0:
            task = asyncio.create_task(self.search_memories(loop_data=loop_data, **kwargs))
        else:
            task = None

        # set to agent to be able to wait for it
        self.agent.set_data(DATA_NAME_TASK, task)
            

    async def search_memories(self, loop_data: LoopData, **kwargs):

        # cleanup
        extras = loop_data.extras_persistent
        if "memories" in extras:
            del extras["memories"]

        # try:
        # show temp info message
        self.agent.context.log.log(
            type="info", content="Searching memories...", temp=True
        )

        # show full util message, this will hide temp message immediately if turned on
        log_item = self.agent.context.log.log(
            type="util",
            heading="Searching memories...",
        )

        # Filter history for query generation to avoid verbose tool outputs
        # Only include human messages (ai=False) for contextual history
        contextual_history_messages = []
        # Get the full history as a flat list of OutputMessage
        full_history_outputs = self.agent.history.output()

        # Import output_text from python.helpers.history for correct formatting
        from python.helpers.history import output_text 
        for output_msg in full_history_outputs[-RecallMemories.HISTORY:]:
            if not output_msg['ai']:  # Only human messages
                # Use output_text to get the string representation of the content
                # output_text expects a list of OutputMessage, so wrap the single output_msg
                contextual_history_messages.append(output_text([output_msg], human_label="USER", ai_label="AI"))
        
        msgs_text = "\n".join(contextual_history_messages)

        system = self.agent.read_prompt(
            "memory.memories_query.sys.md", history=msgs_text
        )

        # log query streamed by LLM
        async def log_callback(content):
            log_item.stream(query=content)

        # call util llm to summarize conversation
        query_raw = await self.agent.call_utility_model(
            system=system,
            message=loop_data.user_message.output_text(), # This is the current user message
            callback=log_callback,
        )
        # Ensure the query is a plain string, not JSON, in case utility model misbehaves
        try:
            parsed_query = self.agent.dirty_json.parse_string(query_raw)
            if isinstance(parsed_query, dict) or isinstance(parsed_query, list):
                query = self.agent.dirty_json.stringify(parsed_query) # Convert JSON back to string
            else:
                query = query_raw # Use as is if not JSON
        except Exception:
            query = query_raw # Fallback if parsing fails

        # get solutions database
        db = await Memory.get(self.agent)

        memories = await db.search_similarity_threshold(
            query=query,
            limit=RecallMemories.RESULTS,
            threshold=RecallMemories.THRESHOLD,
            filter=f"area == '{Memory.Area.MAIN.value}' or area == '{Memory.Area.FRAGMENTS.value}'",  # exclude solutions
        )

        # log the short result
        if not isinstance(memories, list) or len(memories) == 0:
            log_item.update(
                heading="No useful memories found",
            )
            return
        else:
            log_item.update(
                heading=f"{len(memories)} memories found",
            )

        # concatenate memory.page_content in memories:
        memories_text = ""
        for memory in memories:
            memories_text += memory.page_content + "\n\n"
        memories_text = memories_text.strip()

        # log the full results
        log_item.update(memories=memories_text)

        # place to prompt
        memories_prompt = self.agent.parse_prompt(
            "agent.system.memories.md", memories=memories_text
        )

        # append to prompt
        extras["memories"] = memories_prompt

    # except Exception as e:čč
    #     err = errors.format_error(e)
    #     self.agent.context.log.log(
    #         type="error", heading="Recall memories extension error:", content=err
    #     )
