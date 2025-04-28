from autogen import UserProxyAgent, AssistantAgent, GroupChat, GroupChatManager
import subprocess
import os

# Create json for autogen
config_list = [
   {
      'model': 'gpt-4',
      'api_key': 'XXX'
   }
]
# Define the assistant agent using OpenRouter's Mistral model
assistant = AssistantAgent(
    name="GeomAssistant",
    llm_config=config_list,
    "temperature": 0 # Don't be creative
    },
    system_message="""
    You are a command-line assistant for a tool called GEOM.
    
    Your only job is to convert user requests into valid GEOM CLI commands.
    
    You must translate the user input into the GEOM CLI command that should be executed to create
    the desired geometry by the user — no greetings, no descriptions, no explanations.

    ### Examples:
    User: I want to create a silver sphere with radius 10
    Output: -create -sphere Ag 10
    
    User: Make a gold rod along the Z axis, 20 long and 5 wide
    Output: -create -rod Au Z 20 5
    
    User: Graphene disk of radius 25
    Output: -create -graphene disk 25
    
    User: Create a triangular graphene flake with zigzag edges and side length 15
    Output: -create -graphene triangle zigzag 15
    
    User: A gold sphere with a silver shell, core radius 8 and shell radius 10
    Output: -create -sphere -core Au 8 -shell Ag 10
    
    User: Make a dimer of Ag pyramids, each 30 nm high, base side length 20, and dimer distance 10 along +z
    Output: -create -pyramid Ag 30 20 -dimer 10 +z
    """
)

# User proxy agent for interactive CLI input
user_proxy = UserProxyAgent(
    name="User",
    human_input_mode="ALWAYS",
    max_consecutive_auto_reply=1,
    code_execution_config={"work_dir": "."},
    system_message="""Reply TERMINATE if the GEOM command has been solved at full satisfaction. Otherwise, reply CONTINUE, or the reason why the task is not solved yet""" 
)

# Function to run GEOM commands
def run_geom_command(command: str):
    print(f"Running GEOM command: {command}")
    subprocess.run(f"python3 -m geom {command}".split())

# Setup group chat
group_chat = GroupChat(
    agents=[user_proxy, geom_assistant],
    messages=[],
    speaker_selection_method="round_robin"
)

manager = GroupChatManager(groupchat=group_chat)

# Hook into assistant to run the generated command
original_reply = geom_assistant.generate_reply
def hooked_reply(*args, **kwargs):
    try:
        reply = original_reply(*args, **kwargs)
        if isinstance(reply, str):
            run_geom_command(reply)
        elif reply and isinstance(reply, dict) and "content" in reply:
            run_geom_command(reply["content"])

        return reply
    except Exception as e:
        print("❌ Error generating or running command:", e)
        return {"content": "Something went wrong."}

geom_assistant.generate_reply = hooked_reply

# Start the assistant
if __name__ == "__main__":
    user_proxy.initiate_chat(manager, message="Hello! What would you like to create with GEOM?")

