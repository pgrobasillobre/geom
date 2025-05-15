def make_hooked_reply(run_geom_command, original_reply):
    def hooked_reply(*args, **kwargs):
        try:
            user_message = None
            if args and isinstance(args[0], list) and len(args[0]) > 0 and 'content' in args[0][-1]:
                user_message_raw = args[0][-1]['content']
                user_message = user_message_raw.strip().lower()

            reply = original_reply(*args, **kwargs)
            saved_command = reply if isinstance(reply, str) else reply.get("content", "").strip()

            if saved_command:
                if ('error') not in saved_command.lower():
                   run_geom_command(saved_command)
                return {"content": saved_command + "\n\nTERMINATE"}
            else:
                return reply

        except Exception as e:
            print("❌ Error generating or running command:", e)
            return {"content": "Something went wrong."}

    return hooked_reply

