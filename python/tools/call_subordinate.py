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
            "\n\n### Tools available:\n\n"
            "### response:\nFinal answer to user; ends task processing. Use only when done or no task active. Put result in text arg.\n"
            "\nUsage:\n```json\n{\n    \"thoughts\": [\"...\"],\n    \"tool_name\": \"response\",\n    \"tool_args\": {\n        \"text\": \"Answer to the user\"\n    }\n}\n```\n\n"
            "### fetch.fetch:\nFetches a URL from the internet and optionally extracts its contents as markdown.\nUsage:\n```json\n{\n    \"thoughts\": [\"...\"],\n    \"tool_name\": \"fetch.fetch\",\n    \"tool_args\": {\n        \"url\": \"https://example.com\",\n        \"max_length\": 5000\n    }\n}\n```\n\n"
            "     * **Use `fetch.fetch` thoroughly before fallback:**\n"
            "       Start with `fetch.fetch` using `raw=false` from `start_index=0`. If the response is truncated, follow the `start_index` hint and continue fetching more parts until the full page is retrieved.\n"
            "       If 3 consecutive chunks return only boilerplate (e.g., menus, link lists, irrelevant layout), treat `fetch` as ineffective.\n"
            "       If `raw=false` gives no usable data (e.g., empty, broken, or stripped content), retry with `raw=true` from `start_index=0`. If `raw=true` also fails or gives junk, abandon `fetch` and use `browser_agent`.\n"
            "       Do not retry `raw=true` more than once.\n"
            "       Only use `browser_agent` after these conditions are met.\n"
            "### browser_agent:\nSubordinate agent controls playwright browser. Use 'message' for instructions and 'reset' to spawn a new agent. Do not reset if iterating.\nUsage:\n```json\n{\n    \"thoughts\": [\"I need to log in to...\"],\n    \"tool_name\": \"browser_agent\",\n    \"tool_args\": {\n        \"message\": \"Open and log me into example.com\",\n        \"reset\": \"true\"\n    }\n}\n```\n\n"
            "### filesystem.read_file:\nRead the complete contents of a file from the file system.\nUsage:\n```json\n{\n    \"thoughts\": [\"...\"],\n    \"tool_name\": \"filesystem.read_file\",\n    \"tool_args\": {\n        \"path\": \"/path/to/file.txt\"\n    }\n}\n```\n\n"
            "### filesystem.write_file:\nCreate a new file or completely overwrite an existing file with new content.\nUsage:\n```json\n{\n    \"thoughts\": [\"...\"],\n    \"tool_name\": \"filesystem.write_file\",\n    \"tool_args\": {\n        \"path\": \"/path/to/new_file.txt\",\n        \"content\": \"Hello World!\"\n    }\n}\n```\n\n"
            "### filesystem.create_directory:\nCreate a new directory or ensure a directory exists.\nUsage:\n```json\n{\n    \"thoughts\": [\"...\"],\n    \"tool_name\": \"filesystem.create_directory\",\n    \"tool_args\": {\n        \"path\": \"/path/to/new_directory\"\n    }\n}\n```\n\n"
            "### filesystem.list_directory:\nGet a detailed listing of all files and directories in a specified path.\nUsage:\n```json\n{\n    \"thoughts\": [\"...\"],\n    \"tool_name\": \"filesystem.list_directory\",\n    \"tool_args\": {\n        \"path\": \"/path/to/directory\"\n    }\n}\n```\n\n"
            "### filesystem.move_file:\nMove or rename files and directories.\nUsage:\n```json\n{\n    \"thoughts\": [\"...\"],\n    \"tool_name\": \"filesystem.move_file\",\n    \"tool_args\": {\n        \"source\": \"/path/to/old_name.txt\",\n        \"destination\": \"/path/to/new_name.txt\"\n    }\n}\n```\n\n"
            "### filesystem.get_file_info:\nRetrieve detailed metadata about a file or directory.\nUsage:\n```json\n{\n    \"thoughts\": [\"...\"],\n    \"tool_name\": \"filesystem.get_file_info\",\n    \"tool_args\": {\n        \"path\": \"/path/to/file.txt\"\n    }\\n}\\n```\\n\\n"
            "\nExample Response Format:\n" 
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