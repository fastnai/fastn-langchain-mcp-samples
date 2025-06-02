# Fastn MCP and LangChain Integration

This repository demonstrates how to integrate the Fastn MCP (Model Context Protocol) server with the LangChain MCP Adapter and LangChain agent, enabling secure, scalable, and multi-tenant AI-powered automation for SaaS products.

## What is Fastn.ai and UCL?

[Fastn.ai](https://fastn.ai) provides the Fastn UCL (Unified Command Layer), a secure, scalable integration layer that connects AI agents to real-world tools and data. UCL acts as a universal remote control for AI agents, allowing them to interact with external services (like Slack, Gmail, Google Calendar, and more) while maintaining strict security, context, and tenant isolation.

**Fastn provides access to over 1600+ tools** through its extensive library of connectors, enabling your AI agents to automate and orchestrate workflows across a vast ecosystem of SaaS apps and services.

**Key features of Fastn UCL:**
- **Multitenancy:** Native support for true per-tenant isolation and routing, so each customer's data and workflows are kept separate and secure.
- **Centralized Integration:** Manage all connectors, authentication, and routing logic in one place, reducing development and maintenance effort.
- **Scalability:** Easily onboard new customers or support new tools without duplicating workflows.
- **Security:** Built-in authentication, access control, and monitoring for all actions performed by AI agents.
- **Production-Ready:** Fully managed, MCP-compliant platform that handles the complexities of integration, authentication, and tenant isolation for you.

> **Note:** In this repository, we use the term "Fastn MCP" to refer to the Fastn UCL server, as it implements the open Model Context Protocol (MCP) for tool access.

For more details, see the [Fastn UCL documentation](https://docs.fastn.ai/ucl-unified-command-layer/about-fastn-ucl).

---

## Integration Overview

This project shows how to connect a LangChain agent to the Fastn MCP server using the HTTP streamable endpoint (`https://mcp.ucl.dev/shttp/`). This enables your agent to access a wide range of tools and services, with all the benefits of Fastn's multitenant, secure, and scalable architecture.

## What it does

FastnAgent connects to Fastn MCP servers and provides a conversational interface to:

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
- Access to Fastn MCP server(s)

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
python example.py --api-key your_openai_key --server-name fastn --transport streamable_http --url "https://mcp.ucl.dev/shttp/?api_key=YOUR_API_KEY&space_id=YOUR_SPACE_ID" --session user1
```

When prompted, enter your OpenAI API key if not already set in the environment.

## Usage

1. Start the application using the command above
2. The agent will connect to the Fastn MCP server you configure
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

## Fastn MCP Server Configuration Example

```json
{
  "mcpServers": {
    "fastn": {
      "transport": "streamable_http",
      "url": "https://mcp.ucl.dev/shttp/?api_key=YOUR_API_KEY&space_id=YOUR_SPACE_ID"
    }
  }
}
```

### Multi-Tenant Example

```json
{
  "mcpServers": {
    "fastn": {
      "transport": "streamable_http",
      "url": "https://mcp.ucl.dev/shttp/?space_id=YOUR_SPACE_ID&tenant_id=YOUR_TENANT_ID&auth_token=YOUR_AUTH_TOKEN"
    }
  }
}
```

- Replace `YOUR_API_KEY`, `YOUR_SPACE_ID`, `YOUR_TENANT_ID`, and `YOUR_AUTH_TOKEN` with your actual credentials.

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
2. Add new Fastn MCP servers and tools as needed
3. Implement additional error handling or tool-specific logic

## License

MIT 