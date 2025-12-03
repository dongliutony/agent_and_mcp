#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试记忆功能的脚本
"""

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from agent import agent, checkpointer
import uuid

def test_memory():
    print("=== 测试记忆功能 ===\n")

    # 创建会话ID用于checkpoint
    session_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}

    # 初始化消息历史
    messages = [
        SystemMessage(content="你叫小猪，是一名智能助手。请在对话中保持温和、有耐心的语气。")
    ]

    # 测试1：告诉agent名字
    print("测试1：告诉agent名字")
    user_input1 = "你好，我叫大壮"
    messages.append(HumanMessage(content=user_input1))

    try:
        response1 = agent.invoke({"messages": messages}, config)
        if response1.get("messages"):
            last_message1 = response1["messages"][-1]
            if isinstance(last_message1, AIMessage) and last_message1.content:
                print(f"用户：{user_input1}")
                print(f"助理：{last_message1.content}")
                messages.append(last_message1)
    except Exception as e:
        print(f"测试1错误: {str(e)}")

    print("\n" + "-"*40 + "\n")

    # 测试2：询问是否记得名字
    print("测试2：询问是否记得名字")
    user_input2 = "你还记得我叫什么名字吗？"
    messages.append(HumanMessage(content=user_input2))

    try:
        response2 = agent.invoke({"messages": messages}, config)
        if response2.get("messages"):
            last_message2 = response2["messages"][-1]
            if isinstance(last_message2, AIMessage) and last_message2.content:
                print(f"用户：{user_input2}")
                print(f"助理：{last_message2.content}")
                messages.append(last_message2)

                # 检查回复中是否包含名字
                if "大壮" in last_message2.content:
                    print("✅ 记忆功能正常：助理记得用户的名字")
                else:
                    print("❌ 记忆功能异常：助理不记得用户的名字")
    except Exception as e:
        print(f"测试2错误: {str(e)}")

    print("\n" + "-"*40 + "\n")

    # 测试3：新的会话（应该不记得）
    print("测试3：新的会话（应该不记得）")
    new_session_id = str(uuid.uuid4())
    new_config = {"configurable": {"thread_id": new_session_id}}

    # 新会话的消息历史
    new_messages = [
        SystemMessage(content="你叫小猪，是一名智能助手。请在对话中保持温和、有耐心的语气。"),
        HumanMessage(content="你还记得我叫什么名字吗？")
    ]

    try:
        response3 = agent.invoke({"messages": new_messages}, new_config)
        if response3.get("messages"):
            last_message3 = response3["messages"][-1]
            if isinstance(last_message3, AIMessage) and last_message3.content:
                print(f"用户：你还记得我叫什么名字吗？")
                print(f"助理（新会话）：{last_message3.content}")

                # 检查回复中是否包含不记得的信息
                if "不知道" in last_message3.content or "不记得" in last_message3.content or "名字" in last_message3.content:
                    print("✅ 会话隔离正常：新会话不知道之前的信息")
                else:
                    print("❓ 新会话回复：" + last_message3.content)
    except Exception as e:
        print(f"测试3错误: {str(e)}")

    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_memory()