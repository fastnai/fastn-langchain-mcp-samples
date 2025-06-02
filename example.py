#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import os
import argparse
from app import FastnAgent

# Directory for storing chat history
CHAT_HISTORY_DIR = "chat_history"

def save_chat_history(history, session_id="default"):
    """Save chat history to a local file"""
    # Create directory if it doesn't exist
    if not os.path.exists(CHAT_HISTORY_DIR):
        os.makedirs(CHAT_HISTORY_DIR)
    
    # Save chat history to file
    history_file = os.path.join(CHAT_HISTORY_DIR, f"{session_id}.json")
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)
    
    print(f"Chat history saved to {history_file}")

def load_chat_history(session_id="default"):
    """Load chat history from a local file"""
    history_file = os.path.join(CHAT_HISTORY_DIR, f"{session_id}.json")
    
    if os.path.exists(history_file):
        try:
            with open(history_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error reading chat history from {history_file}")
            return []
    else:
        print(f"No chat history found for session {session_id}")
        return []

async def run_interactive():
    """Run an interactive chat session with command-line input"""
    parser = argparse.ArgumentParser(description="FastnAgent Example")
    parser.add_argument("--api-key", help="OpenAI API key")
    parser.add_argument("--server-name", default="fastn", help="MCP server name")
    parser.add_argument("--transport", default="streamable_http", help="MCP transport type")
    parser.add_argument("--url", help="MCP server URL")
    parser.add_argument("--session", default="default", help="Session ID for chat history")
    args = parser.parse_args()
    
    # Get OpenAI API key
    openai_api_key = args.api_key
    if not openai_api_key:
        openai_api_key = input("Enter your OpenAI API key: ")
        if not openai_api_key:
            print("No API key provided. Exiting...")
            return
    
    # Get MCP server configuration
    server_name = args.server_name
    transport = args.transport
    url = args.url
    
    if not url:
        print("\nPlease provide MCP server details:")
        url = input(f"Server URL for {server_name} ({transport}): ")
        if not url:
            print("No server URL provided. Exiting...")
            return
    
    # Initialize the agent with provided configuration
    mcp_servers = {
        server_name: {
            "transport": transport,
            "url": url
        }
    }
    
    # Create and initialize the agent
    print(f"\nInitializing agent with {server_name} server...")
    agent = FastnAgent(openai_api_key, mcp_servers)
    await agent.initialize()
    
    # Load previous chat history if available
    session_id = args.session
    chat_history = load_chat_history(session_id)
    
    print(f"\nWelcome to the FastnAgent Chat!")
    print(f"Session: {session_id}")
    print(f"Loaded {len(chat_history)} previous messages")
    print("Type 'exit' to quit, 'reset' to clear history")
    print("Your messages will be saved automatically")
    
    while True:
        user_input = input("\n> ")
        
        if user_input.lower() == "exit":
            print("Saving chat history and exiting...")
            save_chat_history(chat_history, session_id)
            break
        
        elif user_input.lower() == "reset":
            print("Resetting conversation history...")
            chat_history = []
            save_chat_history(chat_history, session_id)
            agent.reset_conversation()
            continue
        
        print("Processing your message...")
        response = await agent.process_message(user_input, chat_history)
        
        # Update and save chat history
        chat_history = response.get("chat_history", chat_history)
        save_chat_history(chat_history, session_id)
        
        if response.get("status") == "success":
            print(f"\nAgent: {response['assistant_message']}")
            
            # Display tool results if any
            if response.get("tool_results"):
                print("\nTool Results:")
                for tool_id, result in response["tool_results"].items():
                    tool_name = result.get("tool", "unknown")
                    output = result.get("output", "")
                    print(f"  {tool_id}: {tool_name} - {str(output)[:50]}..." 
                          if isinstance(output, str) and len(str(output)) > 50 
                          else f"  {tool_id}: {tool_name} - {output}")
        else:
            print(f"\nError: {response.get('error', 'Unknown error')}")

if __name__ == "__main__":
    # Run interactive chat
    asyncio.run(run_interactive()) 