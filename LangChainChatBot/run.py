from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
# from agent import agent, checkpointer   # 引入你在 agent.py 里的 agent和checkpointer
import os
from agent import agent
from dotenv import load_dotenv
import uuid

load_dotenv(override=True)

def main():
    print("输入 exit 退出对话\n")

    # 创建会话ID用于checkpoint
    session_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}

    # 初始化消息历史
    messages = [
        SystemMessage(content="你叫小猪，是一名智能助手。请在对话中保持温和、有耐心的语气。")
    ]

    # 多轮对话
    while True:
        try:
            user_input = input("你：")
        except EOFError:
            print("\n检测到输入结束，对话结束，再见！")
            break

        if user_input.lower() in {"exit", "quit"}:
            print("对话结束，再见！")
            break

        # 添加用户消息到历史
        messages.append(HumanMessage(content=user_input))

        print("小猪：", end="", flush=True)
        full_reply=""

        # 使用 agent 来处理消息，这样可以使用工具
        try:
            # 调用 agent 并获取响应，传入完整的对话历史和config
            response = agent.invoke({"messages": messages}, config)

            # 获取最新的 AI 消息
            if response.get("messages"):
                last_message = response["messages"][-1]
                if isinstance(last_message, AIMessage) and last_message.content:
                    print(last_message.content, end="", flush=True)
                    full_reply = last_message.content

                    # 将AI回复添加到消息历史
                    messages.append(last_message)
        except Exception as e:
            print(f"发生错误: {str(e)}")
            full_reply = "抱歉，处理您的请求时出现了错误。"

        print("\n" + "-"*40)

if __name__ == "__main__":
    main()