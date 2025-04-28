from autogen import UserProxyAgent, AssistantAgent, GroupChat, GroupChatManager
import subprocess
import os
import json

# ---- Memory Management ----

# Create memory.json if it does not exist
if not os.path.exists("memory.json"):
    with open("memory.json", "w") as f:
        json.dump({}, f)

# Load the memory
with open("memory.json", "r") as f:
    memory = json.load(f)

# ---- End of Memory Management ----


# Function to run GEOM commands
def run_geom_command(command: str):
    subprocess.run(f"python3 -m geom {command}".split())



# Create json for autogen
config_list = [
   {
      'model': 'gpt-4.1-nano',
      'api_key': <enter API key here>
   }
]


# Define the assistant agent
geom_assistant = AssistantAgent(
    name="GeomAssistant",

    llm_config={
        "config_list": config_list,
        "temperature": 0, # Don't be creative
        "seed": 42
    },

    system_message="""
    You are a command-line assistant for a tool called GEOM.
        
    You only job is to translate the user input into the GEOM CLI command that should be executed to create
    the desired geometry by the user — no greetings, no descriptions, no explanations.

    General Rules:

    - Always assume 1 nanometer (nm) = 10 angstroms (Å), which are the required units by GEOM.
    - If the user gives dimensions in nanometers, multiply by 10 to convert to angstroms.
    - If the user does not provide units, assume dimensions are given in angstroms.

    - Only allow alloys and core-shell structures between Silver (Ag) and Gold (Au).
    - If the user asks for an alloy or core-shell with any other element (e.g., Sodium, Iron, etc.), reply exactly:
        "Only Ag/Au alloys are supported in GEOM."
        Do not attempt to generate a command if alloy is invalid.

    - Only allow bowtie creation for tip, pyramid, cone, and microscope.
    - If the user asks for bowtie creation not involving tip, pyramid, cone, or microscope structures, reply exactly:
        "Bowtie creation is only supported for tip, pyramid, cone, or microscope structures"

    - If the user does not provide the main axis in rod creation assume "Z" axis as default.
    - If the user does not provide a mesh size factor for continuum mesh creation, assume a value of 5.0
    - If the user does not provide a base radius/length for cone/pyramid creation use the length provided divided by 2.0
    - If the user wants to create a tip always assume that the a and b parameters definig the parabola of the tip are 0.02 and 0.02, respectively.
    - If the user asks to create a microscope and only specifies the total size, assume:
        - The base side length of the tip pyramid is 20 percent of that size.
        - The height of the pyramid is 30 percent of that size.
        - The parabola parameters a and b are 0.02 and 0.02 respectively.

    Never add explanations, never say "here is the command", only output the command or an error if needed.


    - If the request cannot be fulfilled due to GEOM limitations (e.g. atom type not supported, metallic packing not supported for an specific structure), politely return a short error message and do not output any CLI command.     

    ### Examples:
    User: I want to create a silver sphere with radius 10
    Output: -create -sphere Ag 10
    
    User: Make a gold rod along the Z axis, 20 long and 5 wide
    Output: -create -rod Au Z 20 5
    
    User: Graphene disk of radius 25
    Output: -create -graphene disk 25
    
    User: Create a triangular graphene flake/triangle with zigzag edges and side length 15
    Output: -create -graphene triangle zigzag 15

    User: Create a graphene ring with inner radius of 15 angstroms and outter radius of 3 nm
    Output: -create -graphene ring 30 15

    User: Create a graphene ribbon with a length along X of 20 nm and a length along the Y axis of 15 nm
    Output: -create -graphene rib 200 150
    
    User: A gold sphere with a silver shell, core radius 8 and shell radius 10
    Output: -create -sphere -core Au 8 -shell Ag 10
    
    User: Make a dimer of Ag pyramids, each 30 angstroms high, base side length 20 angstroms, and dimer distance 10 angstroms along +z
    Output: -create -pyramid Ag 30 20 -dimer 10 +z

    User: Create a tip of iron that is 3 nanometers (nm) long
    Output: -create -tip Fe 30 0.02 0.02

    User: Create a microscope of sodium that is 100 angstroms long
    Output: -create -microscope Na 100 0.02 0.02 30 20

    User: Create an icosahedral structure of radius 20 angstroms of gold that contains an alloy percentual of 10 percent of silver
    Output: -create -ico au 20 -alloy ag -percentual 10

    User: Create a bowtie structure considering conical nanoparticles of silver that are 2 nm long with an interdistance of 10 angstroms
    Output: -create -cone ag 20 10

    User: Create a cuboctahedron of gold with a radius of 30 angstroms
    Output: -create -cto au 30

    User: Create a cuboctahedron of silver with a 1.5 nm radius
    Output: -create -idh ag 15

    User: Create a sodium pyramid that is 30 angstroms long
    Output: -create -pyramid na 30 15

    User: Create a sodium pyramid that is 5 nm long
    Output: -create -pyramid na 50 25

    User: Create a sodium pyramid that is 5 nm long and has a base side length of 3 nm
    Output: -create -pyramid na 50 30

    User: Create a core-shell nanorod along the X axis. The inner part is 10 angstroms long and 5 angstroms wide. The outter part is 20 angstroms long and 10 angstroms wide.
    Output: -create -rod X -core ag 10 5 -shell au 20 10

    User: I want to create a continuum mesh with the shape of a sphere of 3 nm radius.
    Output: -create -sphere -continuum 30 5.0

    User: Please, create a continuum mesh for a nanorod along the Y axis that is 1 nm wide and 2 nm long
    Output: -create -rod -continuum Y 20 10 5.0

    User: Please, create a continuum mesh for a nanorod that is 1 nm wide and 2 nm long, also with a mesh size factor of 1.0.
    Output: -create -rod -continuum Z 20 10 1.0
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
        user_message = None

        # Defensive check
        if args and isinstance(args[0], list) and len(args[0]) > 0:
            last_message = args[0][-1]
            if isinstance(last_message, dict) and 'content' in last_message:
                user_message_raw = last_message['content']
                user_message = user_message_raw.strip().lower()

        # Ask LLM (always)
        reply = original_reply(*args, **kwargs)

        if user_message:
            # If user message is valid and found in memory
            if user_message in memory:
                print("🧠 Found in memory (normalized)!")
                command = memory[user_message]
                run_geom_command(command)
                return {"content": command}
            else:
                # Not found, store new answer
                if isinstance(reply, str):
                    memory[user_message] = reply
                    run_geom_command(reply)
                elif isinstance(reply, dict) and "content" in reply:
                    memory[user_message] = reply["content"]
                    run_geom_command(reply["content"])

                with open("memory.json", "w") as f:
                    print("💾 New command learned and stored (normalized)!")
                    json.dump(memory, f, indent=4)

        else:
            # No valid user_message captured (special case)
            print("⚠️ No valid user message found, but running LLM reply...")
            if isinstance(reply, str):
                run_geom_command(reply)
            elif isinstance(reply, dict) and "content" in reply:
                run_geom_command(reply["content"])

        return reply

    except Exception as e:
        print("❌ Error generating or running command:", e)
        return {"content": "Something went wrong."}



geom_assistant.generate_reply = hooked_reply

# Start the assistant
if __name__ == "__main__":
    print("     ============================   ")
    print("     Welcome to GEOM AI Assistant   ")
    print("     ============================   ")
    print("")
    print("     Please type your request (e.g., 'Create a silver sphere of 20 angstroms radius').")
    print("")
    print("     ***************************")
    print("")

    user_proxy.initiate_chat(manager)
