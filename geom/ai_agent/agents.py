from autogen import AssistantAgent, UserProxyAgent
from config import config_list, get_system_prompt

def create_geom_assistant():
    """Create and return the GEOM Assistant agent.

    Returns:
        AssistantAgent: A configured assistant agent capable of translating
                        user input into GEOM CLI commands.
    """

    return AssistantAgent(
        name="GeomAssistant",
        llm_config={
             "config_list": config_list, 
             "temperature": 0.0, 
             "seed": 42
             },
        system_message=get_system_prompt()
    )

def create_user_proxy():
    """Create and return the user proxy agent for human interaction.

    Returns:
        UserProxyAgent: An agent configured to receive human input and
                        terminate after one assistant response.
    """

    return UserProxyAgent(
        name="User",
        human_input_mode="ALWAYS",
        max_consecutive_auto_reply=1,
        code_execution_config={"work_dir": ".", "use_docker": False},
        system_message="Reply TERMINATE if the GEOM command has been solved."
        # Let the model continue asking the user if wants more structure's to be created
        #is_termination_msg=lambda msg: msg.get("content", "").strip().endswith("TERMINATE")
    )

