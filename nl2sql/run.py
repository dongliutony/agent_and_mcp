import uuid
import threading
import sys
from langchain_core.messages import HumanMessage, AIMessage
from nl2sql import create_nl2sql_agent

class LoadingIndicator:
    """加载指示器类，显示旋转动画"""
    def __init__(self, message="思考中"):
        self.message = message
        self.spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self.running = False
        self.thread = None
    
    def _animate(self):
        """动画循环"""
        i = 0
        while self.running:
            char = self.spinner_chars[i % len(self.spinner_chars)]
            sys.stdout.write(f'\r{char} {self.message}...')
            sys.stdout.flush()
            i += 1
            import time
            time.sleep(0.1)
    
    def start(self):
        """开始显示动画"""
        self.running = True
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()
    
    def stop(self):
        """停止显示动画"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.5)
        sys.stdout.write('\r' + ' ' * (len(self.message) + 10) + '\r')
        sys.stdout.flush()

def main():
    """控制台多轮对话主函数"""
    print("=" * 60)
    print("NL2SQL Chatbot - 自然语言查询 Chinook 数据库")
    print("=" * 60)
    print("输入 'exit' 或 'quit' 退出对话\n")
    
    # 创建 agent
    print("正在初始化 Agent...")
    agent = create_nl2sql_agent(verbose=False)
    print("Agent 初始化完成！\n")
    
    # 创建会话ID用于checkpoint（保持对话历史）
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
        
        # 调用 agent 处理用户输入
        try:
            # 显示加载指示器
            loader = LoadingIndicator("AI正在思考")
            loader.start()
            
            try:
                # 使用 agent.invoke() 一次性获取完整响应
                result = agent.invoke(
                    {"messages": [HumanMessage(content=user_input)]},
                    config
                )
            finally:
                # 停止加载指示器
                loader.stop()
            
            print("\nAI: ", end="", flush=True)
            
            # 获取最新的 AI 消息
            if result and "messages" in result and len(result["messages"]) > 0:
                # 从后往前找最后一条有内容的 AI 消息
                last_message = None
                for msg in reversed(result["messages"]):
                    if isinstance(msg, AIMessage):
                        content = getattr(msg, "content", None)
                        # 如果有内容就使用这条消息
                        if content:
                            last_message = msg
                            break
                
                if last_message:
                    content = last_message.content
                    # 处理不同类型的 content
                    if isinstance(content, str):
                        print(content)
                    elif isinstance(content, list):
                        # 处理内容块列表
                        text_parts = []
                        for item in content:
                            if isinstance(item, dict):
                                text_parts.append(str(item.get("text", "")))
                            else:
                                text_parts.append(str(item))
                        print("".join(text_parts))
                    else:
                        print(str(content))
                else:
                    print("抱歉，没有收到有效响应。")
            else:
                print("抱歉，没有收到响应。")
                
        except Exception as e:
            print(f"\n发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "-" * 60 + "\n")

if __name__ == "__main__":
    main()

