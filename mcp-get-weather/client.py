import asyncio
import json 
import logging
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
# from langgraph.prebuilt import create_react_agent
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient 
from langgraph.checkpoint.memory import InMemorySaver


load_dotenv(override=True)
checkpoint = InMemorySaver() 

with open("agent_prompts.txt", "r", encoding="utf-8") as f:
    promt = f.read()

config = {
    "configurable": {"thread_id": "1"},
}

class Configuration:
    def __init__(self) -> None:
        load_dotenv(override=True)
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = ChatOpenAI(model_name="gpt-5-mini", openai_api_key=self.api_key)

    @staticmethod
    def load_servers(file_path = "servers_config.json"):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f).get("mcpServers", {})

# main logic
async def run_chat_loop():
    cfg = Configuration() 
    os.environ["OPENAI_API_KEY"] = cfg.api_key
    servers_cfg = cfg.load_servers() 

    # connect to MCP servers
    mcp_client = MultiServerMCPClient(servers_cfg)
    tools = await mcp_client.get_tools()
    print(f"Loaded {len(tools)} tools from MCP servers") 

    # init LLM model
    model = cfg.model 

    # create agent 
    # agent = create_react_agent(model=model, tools=tools, prompt=promt, checkpointer=checkpoint)
    agent = create_agent(model=model, tools=tools, system_prompt=promt, checkpointer=checkpoint)

    print(f"Agent created: {agent}, input quit to exit")

    # Chat loop
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ["exit", "quit", "bye"]:
            break
        try:
            result = await agent.ainvoke({"messages": [{"role": "user", "content": user_input}]}, config )
            print(f"\nAI: {result['messages'][-1].content}")
        except Exception as e:
            logging.error(f"Error: {e}")
            print("Sorry, something went wrong. Please try again.")

    await mcp_client.cleanup()
    print("Chat session ended. Bye!")

if __name__ == "__main__":
    asyncio.run(run_chat_loop())
    