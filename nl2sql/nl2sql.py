import os
import pathlib
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_openai import ChatOpenAI

from langgraph.checkpoint.memory import InMemorySaver
# from langgraph.types import Command

from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit

from dotenv import load_dotenv

def create_nl2sql_agent(verbose=False):
    """创建并返回配置好的 NL2SQL Agent"""
    load_dotenv(override=True)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-5-mini")

    model = ChatOpenAI(
        model_name="gpt-5-mini",
        openai_api_key=OPENAI_API_KEY
    )
    
    local_db_path = pathlib.Path("Chinook.db") 
    db = SQLDatabase.from_uri(f"sqlite:///{local_db_path}")
    
    if verbose:
        print(f"数据库连接成功")
        print(f"\n数据库方言: {db.dialect}\n")
        print(f"数据库表: {db.get_usable_table_names()}\n")
        print("\n" + "="*60)
        print("数据库Schema（前500字符）：")
        print("="*60)
        print(db.get_table_info()[:500]+ "...")

    toolkit = SQLDatabaseToolkit(db=db, llm=model)
    tools = toolkit.get_tools()

    if verbose:
        print(f"SQL工具包创建成功，共{len(tools)}个工具：\n")
        for tool in tools:
            print(f"{tool.name}")
            print(f"  |- 功能：{tool.description}")
            print()

    # 从 prompt.txt 读取 system_prompt
    prompt_file_path = pathlib.Path("prompt.txt")
    if prompt_file_path.exists():
        with open(prompt_file_path, "r", encoding="utf-8") as f:
            prompt_content = f.read()
        # 移除开头的 "system_prompt = f""" 和结尾的 """（如果存在）
        if prompt_content.startswith('system_prompt = f"""'):
            prompt_content = prompt_content[18:]  # 移除 "system_prompt = f"""
        if prompt_content.endswith('"""'):
            prompt_content = prompt_content[:-3]  # 移除结尾的 """
        prompt_content = prompt_content.strip()
        # 替换占位符
        system_prompt = prompt_content.replace("{db.dialect}", db.dialect)
        system_prompt = system_prompt.replace(
            "{', '.join(db.get_usable_table_names())}", 
            "', '".join(db.get_usable_table_names())
            )
        system_prompt = system_prompt.replace("{5}", "5")
    else:
        # 如果文件不存在，使用默认提示
        system_prompt = "你是一个专业的SQL数据分析Agent。"

    # HITL 中间件
    hitl = HumanInTheLoopMiddleware(
        interrupt_on={"sql_db_query": True},
        description_prefix="⚠️ SQL执行需要人工审批"
    )

    # 创建 Agent（控制台环境，自动执行 SQL，不需要人工审批）
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        # 注释掉 HumanInTheLoopMiddleware，让 SQL 自动执行
        middleware=[hitl],
        checkpointer=InMemorySaver(), 
    )
    
    return agent

if __name__ == "__main__":
    # 如果直接运行此文件，执行初始化并显示信息
    agent = create_nl2sql_agent(verbose=True)
    print("\nAgent 创建成功！")