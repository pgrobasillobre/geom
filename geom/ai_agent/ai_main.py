import logging
from autogen import GroupChat, GroupChatManager
from ai_runner import run_geom_command
from ai_agents import create_geom_assistant, create_user_proxy
from ai_validator import make_hooked_reply

# Suppress the OpenAI API key format warning from autogen
# As far as I have understood, this warning message is due to a bug in autogen
logging.getLogger("autogen.oai.client").setLevel(logging.ERROR)

def main():
    """
    Main function to run the GEOM AI Assistant.

    This script launches a conversational AI assistant for GEOM,
    implemented using Microsoft's AutoGen framework.

    The assistant interprets natural language user requests and 
    translates them into executable GEOM CLI commands via a 
    multi-agent chat interface.

    This function sets up the chat environment, initializes agents,
    and starts the conversational loop.
    """

    print("")
    print("     ============================   ")
    print("     Welcome to GEOM AI Assistant   ")
    print("     ============================   ")
    print("")
    print("     Please type your request:")
    print("")
    print("     (e.g., 'Create a silver sphere of 20 angstroms radius').")
    print("")
    print("     ============================")
    print("")

    geom_assistant = create_geom_assistant()
    user_agent = create_user_proxy()

    # Monkey patching
    original_reply = geom_assistant.generate_reply
    geom_assistant.generate_reply = make_hooked_reply(run_geom_command, original_reply)

    chat = GroupChat(agents=[user_agent, geom_assistant], messages=[], speaker_selection_method="round_robin")
    manager = GroupChatManager(groupchat=chat)

    user_agent.initiate_chat(manager, print_received_message=False)

if __name__ == "__main__":
    main()
