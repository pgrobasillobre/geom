AI Assistant *(new in v1.1.0)*
------------------------------


GEOM now includes an **AI-powered assistant** that understands natural language, translates it into valid GEOM CLI commands, and executes them automatically.

This assistant is built using [Microsoft's AutoGen framework](https://github.com/microsoft/autogen), which enables a multi-agent system to interface with OpenAI’s language models and run commands dynamically.

### 1. Export your OpenAI API key

The assistant requires access to **OpenAI's LLMs**. Make sure you have your API key set:

```
export OPENAI_API_KEY=your-api-key-here
```

> You can obtain an API key from https://platform.openai.com/account/api-keys

### 2. Start the assistant

To launch the chat-based assistant, load the GEOM environment (i.e., with `geom_load`) and run:

```
ai_geom
```

You’ll be greeted with a chat prompt where you can type requests like:


```
Create a gold nanorod along the z axis that is 40 angstroms long and 10 angstroms wide.
```

The assistant will automatically create and execute the corresponding GEOM command for you.

