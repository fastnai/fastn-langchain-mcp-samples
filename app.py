import os
import json
import asyncio
from typing import List, Dict, Any, Optional
import datetime

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

class FastnAgent:
    def __init__(self, openai_api_key: str = None, mcp_servers: Dict[str, Dict[str, str]] = None):
        """
        Initialize the FastnAgent
        
        Args:
            openai_api_key: OpenAI API key
            mcp_servers: Dictionary of MCP servers, e.g. {'fastn': {'transport': 'sse', 'url': 'http://localhost:8000/sse/?api_key=xxx'}}
        """
        self.client = None
        self.agent = None
        self.tools = None
        self.chat_history = []
        self.tool_results = {}  # Store tool results by tool call ID
        
        # Set MCP servers
        self.mcp_servers = mcp_servers
        
        # Set OpenAI API key if provided
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
    
    async def initialize(self):
        """Initialize the MCP client and create the agent"""
        # Configure the MCP client with the provided servers
        self.client = MultiServerMCPClient(self.mcp_servers)
        
        print("\n====== FETCHING TOOLS FROM MCP SERVERS ======")
        # Load tools from all configured servers
        all_tools = []
        
        for server_name, connection in self.mcp_servers.items():
            print(f"\nConnecting to server: {server_name}")
            print(f"Connection type: {connection.get('transport', 'unknown')}")
            print(f"Connection URL: {connection.get('url', 'N/A')}")
            
            try:
                server_tools = await load_mcp_tools(None, connection=connection)
                print(f"✅ Successfully loaded {len(server_tools)} tools from {server_name}")
                all_tools.extend(server_tools)
                
                # Log detailed info about each tool
                for i, tool in enumerate(server_tools):
                    print(f"\nTool #{i+1}: {tool.name}")
                    print(f"  Description: {tool.description}")
                    
                    # Show args schema if available
                    if hasattr(tool, 'args_schema'):
                        print(f"  Args Schema: {tool.args_schema.__name__ if hasattr(tool.args_schema, '__name__') else type(tool.args_schema).__name__}")
            except Exception as e:
                print(f"❌ Error loading tools from {server_name}: {str(e)}")
        
        self.tools = all_tools
        print(f"\n✅ Total tools loaded: {len(self.tools)}")
        
        # Define system prompt for JSON schema validation
        system_prompt = """You are a helpful assistant that processes user requests through various tools.

CRITICAL INSTRUCTION FOR ALL TOOL CALLS:

When a tool requires JSON input, you MUST follow these instructions exactly:

1. DO NOT SEND THE JSON SCHEMA. ALWAYS SEND ACTUAL JSON OBJECTS WITH VALUES.
2. For each property in the schema, provide an appropriate VALUE, not the property definition.
3. Include only the actual data fields and values, not type information, descriptions, or titles.

Here are examples of WRONG (schema) vs CORRECT (values) for different data types:

Example 1 - User Data:
WRONG (schema):
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "User's full name"
    },
    "age": {
      "type": "integer",
      "minimum": 0
    }
  }
}

CORRECT (values):
{
  "name": "John Smith",
  "age": 30
}

Example 2 - Search Parameters:
WRONG (schema):
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Search term"
    },
    "filters": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}

CORRECT (values):
{
  "query": "machine learning",
  "filters": ["articles", "recent"]
}

Example 3 - Nested Objects:
WRONG (schema):
{
  "type": "object",
  "properties": {
    "product": {
      "type": "object",
      "properties": {
        "id": {"type": "string"},
        "price": {"type": "number"}
      }
    }
  }
}

CORRECT (values):
{
  "product": {
    "id": "prod-123",
    "price": 59.99
  }
}

When working with ANY tool:
- Analyze the schema to understand required fields and data types
- Create actual JSON with appropriate values for those fields
- Never include schema metadata like "type", "properties", "description", etc.
- For dates and times, use standard formats (ISO 8601)
- For arrays, include actual array items with appropriate values

IMPORTANT FOR SEQUENTIAL OPERATIONS:
- The results of previous tool calls are stored and available to you
- If you created a document with createDoc, you can refer to the document ID in the tool response
- When updating a document, you MUST use the document ID from the previous createDoc result
- Always check tool responses for IDs, URLs, or other data needed for subsequent operations

This is EXTREMELY important. If you send schemas instead of values, the tools will fail.
"""
        
        # Create a proper ChatPromptTemplate with the system message
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            MessagesPlaceholder(variable_name="messages")
        ])
        
        # Create the agent with proper prompt template
        self.agent = create_react_agent(
            "openai:gpt-4.1-mini", 
            self.tools,
            prompt=prompt
        )
        print("Agent initialized with GPT-4.1-mini and custom system prompt")
    
    def reset_conversation(self):
        """Reset the conversation history"""
        self.chat_history = []
        self.tool_results = {}
        return {"status": "success", "message": "Conversation reset"}
    
    def _extract_tool_results(self, steps):
        """Extract and store tool results from agent's intermediate steps"""
        extracted_results = {}
        
        for step in steps:
            if not isinstance(step, tuple) or len(step) != 2:
                continue
                
            action, result = step
            if not hasattr(action, 'tool') or not hasattr(action, 'tool_input'):
                continue
                
            tool_name = action.tool
            tool_input = action.tool_input
            tool_id = getattr(action, 'id', None) or f"{tool_name}_{len(self.tool_results)}"
            
            # Store the tool result with detailed information
            tool_result = {
                "tool": tool_name,
                "input": tool_input,
                "output": result,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            self.tool_results[tool_id] = tool_result
            extracted_results[tool_id] = tool_result
            
            # For specific tools, extract and store important data for easy reference
            if tool_name == "createDoc" and isinstance(result, str):
                try:
                    # Try to extract document ID from the result
                    if "documentId" in result or "docId" in result:
                        # Parse the result if it's JSON
                        try:
                            parsed_result = json.loads(result)
                            doc_id = parsed_result.get("documentId") or parsed_result.get("docId")
                            if doc_id:
                                self.tool_results["last_document_id"] = doc_id
                                extracted_results["last_document_id"] = doc_id
                        except json.JSONDecodeError:
                            # If not JSON, try to extract using string operations
                            pass
                except Exception as e:
                    print(f"Error extracting document ID: {e}")
        
        return extracted_results
    
    async def process_message(self, message: str, previous_messages: List[Dict[str, Any]] = None):
        """
        Process a user message and get a response from the agent
        
        Args:
            message: User message
            previous_messages: List of previous messages in the conversation
            
        Returns:
            Dict containing:
            - assistant_message: The assistant's response
            - tool_results: Results of any tool calls made
            - chat_history: Updated chat history
        """
        if not self.agent:
            return {"error": "Agent not initialized. Please initialize first."}
        
        # Use provided chat history or start fresh
        if previous_messages is not None:
            self.chat_history = previous_messages
        
        # Add user message to history
        self.chat_history.append({"role": "user", "content": message})
        
        # Convert chat history to LangChain message format and validate message sequence
        messages = []
        assistant_with_tool_calls = None
        
        # First pass: scan for any tool messages without preceding tool_calls
        for i, msg in enumerate(self.chat_history):
            # Check if this is a tool message without a preceding assistant message with tool_calls
            if msg["role"] == "tool":
                if i == 0 or self.chat_history[i-1]["role"] != "assistant" or "tool_calls" not in self.chat_history[i-1]:
                    # Skip invalid tool messages that don't have a preceding assistant with tool_calls
                    print(f"WARNING: Skipping invalid tool message that has no preceding assistant with tool_calls")
                    continue
        
        # Second pass: build valid message sequence
        tool_call_ids_seen = set()
        
        for msg in self.chat_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            
            elif msg["role"] == "assistant":
                # Capture tool_calls for validation
                if "tool_calls" in msg:
                    assistant_with_tool_calls = msg
                    tool_call_ids = [tc.get("id") for tc in msg["tool_calls"]] if "tool_calls" in msg else []
                    tool_call_ids_seen = set()  # Reset seen tool call IDs for this assistant message
                    
                    # Add the assistant message with tool_calls
                    messages.append(AIMessage(
                        content=msg["content"],
                        tool_calls=msg["tool_calls"]
                    ))
                else:
                    # Regular assistant message without tool_calls
                    messages.append(AIMessage(content=msg["content"]))
                    assistant_with_tool_calls = None  # Reset
            
            elif msg["role"] == "tool" and assistant_with_tool_calls is not None:
                # Only include tool messages that respond to a preceding assistant's tool_call
                tool_call_id = msg.get("tool_call_id")
                
                # Validate this tool message corresponds to one of the assistant's tool_calls
                valid_tool_call_ids = [tc.get("id") for tc in assistant_with_tool_calls.get("tool_calls", [])]
                
                if tool_call_id in valid_tool_call_ids and tool_call_id not in tool_call_ids_seen:
                    # Add a valid tool message
                    tool_call_ids_seen.add(tool_call_id)
                    messages.append(ToolMessage(
                        content=msg["content"],
                        tool_call_id=tool_call_id,
                        name=msg.get("name")
                    ))
        
        # Get response from agent
        try:
            response = await self.agent.ainvoke({"messages": messages})
            
            # Extract and store tool results if available
            new_tool_results = {}
            if "intermediate_steps" in response:
                new_tool_results = self._extract_tool_results(response["intermediate_steps"])
            
            # Process the response
            last_assistant_message = None
            tool_calls_info = []
            
            for msg in response["messages"]:
                if isinstance(msg, AIMessage):
                    last_assistant_message = msg.content
                    
                    # Capture tool calls for storage
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        tool_calls_info = msg.tool_calls
                
                # Store tool messages
                if isinstance(msg, ToolMessage) and msg.tool_call_id:
                    self.chat_history.append({
                        "role": "tool",
                        "name": msg.name,
                        "content": msg.content,
                        "tool_call_id": msg.tool_call_id
                    })
            
            # Add assistant message to history
            if last_assistant_message is not None:
                if tool_calls_info:
                    # Store assistant message with tool calls
                    self.chat_history.append({
                        "role": "assistant", 
                        "content": last_assistant_message,
                        "tool_calls": tool_calls_info
                    })
                else:
                    # Store regular assistant message
                    self.chat_history.append({
                        "role": "assistant", 
                        "content": last_assistant_message
                    })
            
            # Return structured response for API usage
            return {
                "status": "success",
                "assistant_message": last_assistant_message or "No response from assistant",
                "tool_results": new_tool_results,
                "chat_history": self.chat_history
            }
        
        except Exception as e:
            error_message = f"Error: {str(e)}"
            print(error_message)
            return {
                "status": "error",
                "error": error_message,
                "chat_history": self.chat_history
            }
    
    def get_tool_results(self):
        """Get all stored tool results"""
        return self.tool_results