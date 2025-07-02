from agent import Agent, UserMessage, AgentContext, AgentContextType
from python.helpers.tool import Tool, Response


class Delegation(Tool):

    async def execute(self, message="", reset="", **kwargs):
        # create subordinate agent using the data object on this agent and set superior agent to his data object
        if (
            self.agent.get_data(Agent.DATA_NAME_SUBORDINATE) is None
            or str(reset).lower().strip() == "true"
        ):
            # MODIFIED: Create a new AgentContext but pass the superior's log object
            # This allows the subordinate to have its own context (for history, etc.)
            # but direct its output to the superior's chat UI.
            sub_context = AgentContext(self.agent.config, type=AgentContextType.TASK, log=self.agent.context.log)
            sub = Agent(
                self.agent.number + 1, self.agent.config, sub_context
            )
            sub.set_data(Agent.DATA_NAME_SUPERIOR, self.agent)
            print(f"[DEBUG call_subordinate]: Superior set on subordinate. Subordinate's DATA_NAME_SUPERIOR: {sub.get_data(Agent.DATA_NAME_SUPERIOR) is not None}")
            self.agent.set_data(Agent.DATA_NAME_SUBORDINATE, sub)

        # add user message to subordinate agent
        subordinate: Agent = self.agent.get_data(Agent.DATA_NAME_SUBORDINATE)

        # Define and set the one-time system prompt for the subordinate
        # MODIFIED: Giving the subordinate the same response formatting instructions as Agent 0
        subordinate_system_prompt = (
            "You are a subordinate agent. Your responses must always be valid JSON with the following fields: `thoughts`, `tool_name`, and `tool_args`. "
            "You should provide your thoughts before execution and then specify the tool to use with its arguments. "
            "No text should appear before or after the JSON output. Always output full file paths when interacting with the file system."
            "\n\nExample Response Format:\n" 
            "```json\n" 
            "{\n" 
            "    \"thoughts\": [\n" 
            "        \"This is my thought process.\",\n" 
            "        \"I am planning to use a tool.\"\n" 
            "    ],\n" 
            "    \"tool_name\": \"response\",\n" 
            "    \"tool_args\": {\n" 
            "        \"text\": \"This is my final answer or the result of my task.\"\n" 
            "    }\n" 
            "}\n" 
            "```"
        )
        subordinate.set_data("_one_time_system_prompt", subordinate_system_prompt)

        subordinate.hist_add_user_message(UserMessage(message=message, attachments=[]))
        # run subordinate monologue
        result = await subordinate.monologue()

        # Prepare debug info to be included in the response
        debug_info = {
            "subordinate_history_length": len(subordinate.history.output()),
            "subordinate_one_time_prompt_set": subordinate.get_data("_one_time_system_prompt") is not None,
            "subordinate_is_subordinate_flag": subordinate.get_data(Agent.DATA_NAME_SUPERIOR) is not None
        }

        # Append debug info to the result message (as a separate section)
        response_message = f"Subordinate response: {result}\n\n[SUBORDINATE_DEBUG]: {debug_info}"

        # result
        return Response(message=response_message, break_loop=False)