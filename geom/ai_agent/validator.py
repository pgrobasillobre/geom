def make_hooked_reply(run_geom_command, original_reply):
    """
    Creates a wrapped version of an assistant's `generate_reply` method that injects
    post-processing logic for GEOM command execution and controlled termination.

    This function is intended to be used to monkey-patch an assistant agent's
    `generate_reply` method in AutoGen. When the assistant is called to reply during
    a chat (via `generate_reply(history)`), the returned `hooked_reply` function:

    1. Calls the original `generate_reply` to get the assistant's output.
    2. Extracts the CLI command from the reply.
    3. Executes the command using `run_geom_command()` if it's not an error.
    4. Appends 'TERMINATE' to the reply to signal AutoGen to stop the loop.

    Args:
        run_geom_command (Callable[[str], None]): A function that executes a valid GEOM command string.
        original_reply (Callable): The original `generate_reply` method of the assistant.

    Returns:
        Callable: A wrapped `generate_reply` function that handles command execution
        and forces termination signaling.

    Example Usage:
        geom_assistant.generate_reply = make_hooked_reply(run_geom_command, geom_assistant.generate_reply)
    """

    def hooked_reply(*args, **kwargs):
        try:
            reply = original_reply(*args, **kwargs)
            saved_command = reply if isinstance(reply, str) else reply.get("content", "").strip()

            if saved_command:
                if 'error' not in saved_command.lower():
                    run_geom_command(saved_command)
                return {"content": saved_command + "\n\nTERMINATE"}
            else:
                return reply

        except Exception as e:
            print("❌ Error generating or running command:", e)
            return {"content": "Something went wrong."}

    return hooked_reply

