# FastnAgent with MCP Tools

A powerful agent for accessing and using MCP (Model Context Protocol) tools through natural language commands. This project enables users to interact with various tools like MongoDB, Gmail, Google Calendar, and LinkedIn through a simple chat interface.

## What it does

FastnAgent connects to MCP servers and provides a conversational interface to:

- Query and manipulate MongoDB databases
- Send and read emails through Gmail
- Create and manage Google Calendar events
- Post and interact with LinkedIn content
- And any other MCP-compatible tools

The agent uses LangChain and GPT models to interpret natural language commands and convert them into the appropriate tool calls, making complex operations more accessible.

## Setup

### Prerequisites

- Python 3.8+
- OpenAI API key
- Access to MCP server(s)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/fastnai/fastn-langchain-mcp-samples.git
cd fastn-langchain-mcp-samples
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Create a `.env` file with your OpenAI API key:

```
OPENAI_API_KEY=your_openai_api_key_here
```

### Running the application

Run the application with:

```bash
python example.py
```

You can also provide arguments directly:

```bash
python example.py --api-key your_openai_key --server-name fastn --transport streamable_http --url "https://your-mcp-server.com/shttp/?api_key=your_api_key&space_id=your_space_id" --session user1
```

When prompted, enter your OpenAI API key if not already set in the environment.

## Usage

1. Start the application using the command above
2. The agent will connect to the default MCP server or the ones you configure
3. Type your requests in natural language, for example:
   - "Show me the last 10 emails in my inbox"
   - "Create a calendar event for tomorrow at 2pm titled 'Team Meeting'"
   - "Query my MongoDB database for all users who signed up last month"
4. The agent will process your request, make the necessary tool calls, and return the results

## API Usage

You can also use FastnAgent as an API in your own applications:

```python
from app import FastnAgent
import asyncio

async def example():
    agent = FastnAgent(openai_api_key="your_key_here")
    await agent.initialize()
    
    response = await agent.process_message("Create a new Google Doc titled 'Meeting Notes'")
    print(response["assistant_message"])

asyncio.run(example())
```

## Advanced Configuration

### Standard Configuration

You can configure multiple MCP servers by providing a dictionary when initializing FastnAgent:

```python
mcp_servers = {
    "fastn": {
        "transport": "streamable_http",
        "url": "https://your-mcp-server.com/shttp/?api_key=your_api_key&space_id=your_space_id"
    },
    "other_server": {
        "transport": "sse",
        "url": "http://another-server.com/sse/?api_key=another_key"
    }
}

agent = FastnAgent(openai_api_key="your_key", mcp_servers=mcp_servers)
```

### Multi-Tenant Configuration

FastnAgent supports multi-tenant configurations for organizations that need to manage multiple workspaces or users.

#### Workspace URL Configuration

```json
{
  "mcpServers": {
    "fastn": {
      "transport": "streamable_http",
      "url": "https://your-mcp-server.com/shttp/?api_key=your_api_key&space_id=your_space_id"
    }
  }
}
```

#### Multi-Tenant Base URL Configuration

```json
{
  "mcpServers": {
    "fastn": {
      "transport": "streamable_http",
      "url": "https://your-mcp-server.com/shttp/?space_id=your_space_id&tenant_id=your_tenant_id&auth_token=your_auth_token"
    }
  }
}
```

To use these configurations in your code:

```python
import json

# Load configuration from a file
with open('config.json', 'r') as f:
    config = json.load(f)

# Initialize the agent with the loaded configuration
agent = FastnAgent(openai_api_key="your_key", mcp_servers=config["mcpServers"])
await agent.initialize()
```

## Development

To extend the functionality:

1. Modify the `FastnAgent` class in `app.py` to add new features
2. Add new MCP servers and tools as needed
3. Implement additional error handling or tool-specific logic

## License

MIT 