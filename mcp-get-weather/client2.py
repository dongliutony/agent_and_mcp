import asyncio
import json 
import logging
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient 
from langgraph.checkpoint.memory import InMemorySaver


"""
User open source tools: Filesystem MCP Server 
"""



load_dotenv(override=True)
checkpoint = InMemorySaver() 

with open("agent_prompts.txt", "r", encoding="utf-8") as f:
    promt = f.read()

# Use a thread_id for the session
import time
thread_id = f"thread_{int(time.time())}"

class Configuration:
    def __init__(self) -> None:
        load_dotenv(override=True)
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = ChatOpenAI(model_name="gpt-5-mini", openai_api_key=self.api_key)

    @staticmethod
    def load_servers(file_path = "servers_config2.json"):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f).get("mcpServers", {})

# main logic
async def run_chat_loop():
    cfg = Configuration() 
    os.environ["OPENAI_API_KEY"] = cfg.api_key
    servers_cfg = cfg.load_servers() 

    # Create MCP client (no need for context manager or manual cleanup)
    mcp_client = MultiServerMCPClient(servers_cfg)
    all_tools = await mcp_client.get_tools()
    
    # Filter out problematic tools that have parameter validation issues
    # list_directory_with_sizes has issues with langchain_mcp_adapters parameter conversion
    problematic_tools = {"list_directory_with_sizes"}
    tools = [tool for tool in all_tools if tool.name not in problematic_tools]
    
    print(f"Loaded {len(tools)} tools from MCP servers (filtered {len(all_tools) - len(tools)} problematic tools)") 

    # init LLM model
    model = cfg.model 

    # create agent 
    # agent = create_react_agent(model=model, tools=tools, prompt=promt, checkpointer=checkpoint)
    agent = create_agent(model=model, tools=tools, system_prompt=promt, checkpointer=checkpoint)

    print(f"Agent created: {agent}, input quit to exit")
    
    # Current thread_id (will be updated if checkpoint state gets corrupted)
    current_thread_id = thread_id

    # Chat loop
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ["exit", "quit", "bye"]:
            break
        try:
            config = {
                "configurable": {"thread_id": current_thread_id},
            }
            result = await agent.ainvoke({"messages": [{"role": "user", "content": user_input}]}, config )
            # Get the last message content
            if result and "messages" in result and len(result["messages"]) > 0:
                last_message = result["messages"][-1]
                if hasattr(last_message, 'content'):
                    print(f"\nAI: {last_message.content}")
                elif isinstance(last_message, dict) and 'content' in last_message:
                    print(f"\nAI: {last_message['content']}")
                else:
                    print(f"\nAI: {last_message}")
            else:
                print("\nAI: (无响应)")
                
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Error: {e}")
            
            # Provide more helpful error messages for common issues
            if "list_directory_with_sizes" in error_msg or "Invalid structured content" in error_msg:
                print("\n抱歉，获取文件大小信息的工具暂时不可用。")
                print("您可以使用 'list_directory' 工具来列出文件，但可能无法显示文件大小。")
            elif "tool_calls" in error_msg and "must be followed" in error_msg:
                print("\n检测到对话历史状态不一致，正在切换到新的对话线程...")
                # Switch to a new thread_id to reset the checkpoint state
                current_thread_id = f"thread_{int(time.time())}"
                print(f"已切换到新线程: {current_thread_id}")
                print("请重新输入您的问题。")
            else:
                print("Sorry, something went wrong. Please try again.")
                print(f"Error details: {error_msg[:200]}")  # Show first 200 chars of error

    print("Chat session ended. Bye!")

if __name__ == "__main__":
    asyncio.run(run_chat_loop())
    