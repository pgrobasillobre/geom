from autogen import GroupChat, GroupChatManager
from runner import run_geom_command
from agents import create_geom_assistant, create_user_proxy
from validator import make_hooked_reply

if __name__ == "__main__":

    print("")
    print("     ============================   ")
    print("     Welcome to GEOM AI Assistant   ")
    print("     ============================   ")
    print("")
    print("     Please type your request (e.g., 'Create a silver sphere of 20 angstroms radius').")
    print("")
    print("     ============================")
    print("")

    geom_assistant = create_geom_assistant()
    user_agent = create_user_proxy()

    original_reply = geom_assistant.generate_reply
    geom_assistant.generate_reply = make_hooked_reply(run_geom_command, original_reply)

    chat = GroupChat(agents=[user_agent, geom_assistant], messages=[], speaker_selection_method="round_robin")
    manager = GroupChatManager(groupchat=chat)
    user_agent.initiate_chat(manager)

