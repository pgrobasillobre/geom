from autogen import AssistantAgent, UserProxyAgent
from config import config_list, get_system_prompt

def create_geom_assistant():
    return AssistantAgent(
        name="GeomAssistant",
        llm_config={"config_list": config_list, "temperature": 0.0, "seed": 42},
        system_message=get_system_prompt()
    )

def create_user_proxy():
    return UserProxyAgent(
        name="User",
        human_input_mode="ALWAYS",
        max_consecutive_auto_reply=1,
        code_execution_config={"work_dir": ".", "use_docker": False},
        system_message="Reply TERMINATE if the GEOM command has been solved.",
        is_termination_msg=lambda msg: msg.get("content", "").strip().endswith("TERMINATE")
    )

