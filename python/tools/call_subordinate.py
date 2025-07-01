from agent import Agent, UserMessage, AgentContext, AgentContextType
from python.helpers.tool import Tool, Response


class Delegation(Tool):

    async def execute(self, message="", reset="", **kwargs):
        # create subordinate agent using the data object on this agent and set superior agent to his data object
        if (
            self.agent.get_data(Agent.DATA_NAME_SUBORDINATE) is None
            or str(reset).lower().strip() == "true"
        ):
            sub_context = AgentContext(self.agent.config, type=AgentContextType.TASK)
            sub = Agent(
                self.agent.number + 1, self.agent.config, sub_context
            )
            sub.set_data(Agent.DATA_NAME_SUPERIOR, self.agent)
            print(f"[DEBUG call_subordinate]: Superior set on subordinate. Subordinate's DATA_NAME_SUPERIOR: {sub.get_data(Agent.DATA_NAME_SUPERIOR) is not None}")
            self.agent.set_data(Agent.DATA_NAME_SUBORDINATE, sub)

        # add user message to subordinate agent
        subordinate: Agent = self.agent.get_data(Agent.DATA_NAME_SUBORDINATE)

        # Define and set the one-time system prompt for the subordinate
        subordinate_system_prompt = "You are a specialized subordinate AI. You have no prior chat history or external memory access. Your sole purpose is to respond to the immediate task given by your superior. Confirm you have no prior chat history or external memory and state your purpose. Respond in a concise JSON format: { \"confirmation\": \"<yes/no>\", \"purpose\": \"<your purpose>\", \"history_length\": <length of history>, \"actual_system_prompt_start\": \"<start of system prompt>\" }"
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
