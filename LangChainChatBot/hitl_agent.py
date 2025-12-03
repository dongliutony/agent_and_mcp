import os
from dotenv import load_dotenv
load_dotenv(override=True)
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults 
# from langgraph.checkpoint.memory import InMemorySaver

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
model = ChatOpenAI(
    model_name="gpt-5-mini",
    openai_api_key=OPENAI_API_KEY
)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
web_search = TavilySearchResults(max_results=2)

# 创建 Agent，接入 HumanInTheLoopMiddleware
agent = create_agent(
    model=model,
    tools=[web_search],
    # checkpointer=InMemorySaver(),
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                # 拦截 Tavily 搜索工具执行前，要求人工确认
                "tavily_search_results_json": {
                    "allowed_decisions": ["approve", "edit", "reject"],
                    "description": lambda tool_name, tool_input, state: (
                        f"🔍 模型准备执行 Tavily 搜索：'{tool_input.get('query', '')}'"
                    ),
                }
            },
            description_prefix="⚠️ 工具执行需要人工审批"
        )
    ],
)