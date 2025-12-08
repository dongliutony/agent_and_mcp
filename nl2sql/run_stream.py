import uuid
import sys
import threading
import time
from typing import Dict, Any

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from nl2sql import create_nl2sql_agent


class LoadingIndicator:
    """简单的控制台 Loading 动画（独立线程）"""
    def __init__(self, message: str = "AI 正在思考"):
        self.message = message
        self.spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self.running = False
        self.thread: threading.Thread | None = None

    def _animate(self):
        i = 0
        while self.running:
            char = self.spinner_chars[i % len(self.spinner_chars)]
            sys.stdout.write(f"\r{char} {self.message}...")
            sys.stdout.flush()
            i += 1
            time.sleep(0.1)

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()

    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.5)
        # 清掉一行 spinner
        sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r")
        sys.stdout.flush()


def stream_once(agent, inputs, config, label: str = "AI") -> Dict[str, Any]:
    """
    对 agent 执行一次流式调用（values 模式）：

    - 使用 stream_mode="values"
    - 遇到 messages 就增量输出最后一条消息内容（token-style 流式）
    - 遇到 __interrupt__ 就返回 {"__interrupt__": ...}
    """
    loader = LoadingIndicator("AI 正在思考")
    loader.start()

    printed_anything = False
    label_printed = False
    interrupt_list = None

    # 用来记录“已经打印到哪”，实现增量输出
    last_text = ""

    try:
        for step in agent.stream(
            inputs,
            config=config,
            stream_mode="values",   # ✅ 继续用 values，才能看到 __interrupt__
        ):
            # 1) 先处理 HITL 中断：step 中直接带 __interrupt__
            if "__interrupt__" in step:
                interrupt_list = step["__interrupt__"]
                if loader.running:
                    loader.stop()
                print("\n[系统] 检测到需要人工审批的工具调用。\n")
                break

            # 2) 正常消息：step 中有 messages
            if "messages" in step:
                messages = step["messages"]
                if not messages:
                    continue
                last_msg = messages[-1]
                content = getattr(last_msg, "content", "")
                if not content:
                    continue

                # content 统一转成字符串 full_text
                if isinstance(content, str):
                    full_text = content
                elif isinstance(content, list):
                    parts = []
                    for item in content:
                        if isinstance(item, dict):
                            parts.append(str(item.get("text", "")))
                        else:
                            parts.append(str(item))
                    full_text = "".join(parts)
                else:
                    full_text = str(content)

                # 第一次真正有输出内容 → 停掉 loader，打印 label
                if not label_printed and full_text:
                    label_printed = True
                    if loader.running:
                        loader.stop()
                    print(f"\n{label}: ", end="", flush=True)

                # 增量输出：只把“新追加的部分”打印出来
                if len(full_text) > len(last_text):
                    delta = full_text[len(last_text):]
                    last_text = full_text

                    if delta:
                        printed_anything = True
                        sys.stdout.write(delta)
                        sys.stdout.flush()

    finally:
        if loader.running:
            loader.stop()

        # 如果这轮有输出内容，再补一个换行
        if printed_anything:
            sys.stdout.write("\n")
            sys.stdout.flush()
        elif interrupt_list is None:
            # 没输出、也没中断
            print(f"\n{label}: （没有输出内容）")

    # 如果有中断，返回给外层处理
    if interrupt_list is not None:
        return {"__interrupt__": interrupt_list}
    else:
        # 这一轮没有 HITL，就返回空 dict
        return {}


def handle_hitl_once(agent, state_values: Dict[str, Any], config) -> Dict[str, Any]:
    """
    处理一次 HITL 中断：
    - state_values 现在就是 {"__interrupt__": [...]} 这种形态
    - 在 console 里让用户 approve/reject
    - 用 Command(resume=...) 再流式一次
    """
    if "__interrupt__" not in state_values:
        return state_values

    interrupt_list = state_values["__interrupt__"]
    if not interrupt_list:
        return state_values

    first_interrupt = interrupt_list[0]
    interrupt_value = getattr(first_interrupt, "value", first_interrupt)

    action_requests = interrupt_value.get("action_requests", [])
    review_configs = interrupt_value.get("review_configs", [])

    config_map = {cfg["action_name"]: cfg for cfg in review_configs}

    decisions = []

    print("\n=== 检测到需要人工审批的 SQL 调用 ===")
    for idx, action in enumerate(action_requests, start=1):
        name = action["name"]
        args = action["args"]
        review_cfg = config_map.get(name, {})
        allowed = review_cfg.get("allowed_decisions", ["approve", "reject", "edit"])

        print(f"\n[{idx}] 工具: {name}")
        print(f"     参数: {args}")
        print(f"     允许决策: {', '.join(allowed)}")

        # 简化：目前只支持 approve / reject
        while True:
            choice = input("     是否执行该 SQL? (a=执行, r=拒绝) ").strip().lower()
            if choice in ("a", "r"):
                break
            print("     请输入 a 或 r。")

        if choice == "a":
            decisions.append({"type": "approve"})
        else:
            decisions.append({"type": "reject"})

    print("\n已记录人工决策，正在继续执行...\n")

    # 用 Command(resume=...) + 同一个 thread_id 继续执行
    resumed_values = stream_once(
        agent,
        Command(resume={"decisions": decisions}),
        config,
        label="AI(继续)",
    )
    return resumed_values


def main():
    """控制台多轮对话主函数（HITL + 流式输出 + LoadingIndicator）"""
    print("=" * 60)
    print("NL2SQL Chatbot - 自然语言查询 Chinook 数据库")
    print("=" * 60)
    print("输入 'exit' 或 'quit' 退出对话\n")

    # 创建 agent
    print("正在初始化 Agent...")
    agent = create_nl2sql_agent(verbose=False)
    print("Agent 初始化完成！\n")

    # 创建会话 ID（thread_id 用来关联 checkpoint）
    session_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}

    print(f"会话ID: {session_id[:8]}...")
    print("-" * 60)
    print()

    # 多轮对话循环
    while True:
        try:
            user_input = input("你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n检测到输入结束，对话结束，再见！")
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit", "bye", "退出"]:
            print("\n对话结束，再见！")
            break

        try:
            # 第一次：用户输入 -> 流式输出（带 spinner + 增量打印）
            state_values = stream_once(
                agent,
                {"messages": [HumanMessage(content=user_input)]},
                config,
                label="AI",
            )

            # 如果有 __interrupt__，就循环：人工审批 + resume + 再流式
            while "__interrupt__" in state_values:
                state_values = handle_hitl_once(agent, state_values, config)

        except Exception as e:
            print(f"\n发生错误: {str(e)}")
            import traceback
            traceback.print_exc()

        print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    main()
