# Movie Agent with database
Reason and Act Agent written with Langchain/Langgraph, using LLM and tools which work with database.

# Database
SQL Lite database filled with data from open sources. There is some 500+ movies in it. I compiled the data myself - feel free to use.

# Specs
The chatbot is explicitly instructed to use data from this database when chatting with user.

# Running the code

## API Key
Please create an `.env` file and place your OpenAI API Key there.

## Run
```bash
uv sync
uv run ./main.py
```

License MIT