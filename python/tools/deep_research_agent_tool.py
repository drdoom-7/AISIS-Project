from agent import Agent, UserMessage, AgentContext, AgentContextType, AgentConfig
from python.helpers.tool import Tool, Response
from copy import deepcopy


class DeepResearchAgent(Tool):

    async def execute(self, message="", reset="", **kwargs):
        # create subordinate agent using the data object on this agent and set superior agent to his data object
        if (
            self.agent.get_data(Agent.DATA_NAME_SUBORDINATE) is None
            or str(reset).lower().strip() == "true"
        ):
            # Create a new AgentConfig for the subordinate
            # Use deepcopy to ensure it's a new independent object
            sub_config = deepcopy(self.agent.config)
            # Set the prompts_subdir for the deep research agent
            sub_config.prompts_subdir = "deep-research-agent3"

            # Create a new AgentContext but pass the superior's log object
            # This allows the subordinate to have its own context (for history, etc.)
            # but direct its output to the superior's chat UI.
            sub_context = AgentContext(sub_config, type=AgentContextType.TASK, log=self.agent.context.log)
            sub = Agent(
                self.agent.number + 1, sub_config, sub_context
            )
            sub.set_data(Agent.DATA_NAME_SUPERIOR, self.agent)
            print(f"[DEBUG deep_research_agent_tool]: Superior set on subordinate. Subordinate's DATA_NAME_SUPERIOR: {sub.get_data(Agent.DATA_NAME_SUPERIOR) is not None}")
            self.agent.set_data(Agent.DATA_NAME_SUBORDINATE, sub)

        # add user message to subordinate agent
        subordinate: Agent = self.agent.get_data(Agent.DATA_NAME_SUBORDINATE)

        # No need to set a one-time system prompt; it will be loaded from prompts_subdir
        # subordinate.set_data("_one_time_system_prompt", subordinate_system_prompt)

        subordinate.hist_add_user_message(UserMessage(message=message, attachments=[]))
        # run subordinate monologue
        result = await subordinate.monologue()

        # Prepare debug info to be included in the response
        debug_info = {
            "subordinate_history_length": len(subordinate.history.output()),
            "subordinate_prompts_subdir": subordinate.config.prompts_subdir,
            "subordinate_is_subordinate_flag": subordinate.get_data(Agent.DATA_NAME_SUPERIOR) is not None
        }

        # Append debug info to the result message (as a separate section)
        response_message = f"Subordinate response: {result}\n\n[SUBORDINATE_DEBUG]: {debug_info}"

        # result
        return Response(message=response_message, break_loop=False)