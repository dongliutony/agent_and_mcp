import asyncio
import sys
from client import WeatherChatBot

async def test_client():
    """测试客户端功能"""
    bot = WeatherChatBot()

    try:
        # 初始化
        print("正在初始化天气助手...")
        await bot.initialize()
        print("正在加载工具...")
        await bot.load_tools()
        print("天气助手已就绪！")
        print("=" * 50)

        # 测试天气查询
        print("测试1: 查询天气")
        response = await bot.chat("北京天气怎么样？")
        print(f"助手: {response}")
        print()

        # 测试写文件
        print("测试2: 写入文件")
        response = await bot.chat("请帮我记录：今天天气不错")
        print(f"助手: {response}")
        print()

        # 测试上下文记忆
        print("测试3: 测试记忆功能")
        response = await bot.chat("我刚才让你记录了什么？")
        print(f"助手: {response}")
        print()

        print("所有测试完成！")

    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
    finally:
        # 清理资源
        await bot.cleanup()

if __name__ == "__main__":
    asyncio.run(test_client())