# Movie Agent with database
AI Agent written with Langchain/Langgraph

# Database
SQL Lite database filled with data from open sources. There is some 500+ movies in it. I compiled the data myself - feel free to use.

# Specs
The agent is explicitly instructed to use data from this database when talking with user.

# Running the code

## API Key
Please create an ````.env```` file and place your Open AI API Key there.

## Run
````bash````
uv sync
uv run ./main.py
````bash````

License MIT