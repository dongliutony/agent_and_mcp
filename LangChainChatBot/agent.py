import os
from dotenv import load_dotenv
load_dotenv(override=True)
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool
# from langgraph.checkpoint.memory import MemorySaver
import requests, json
from langchain_community.tools.tavily_search import TavilySearchResults 

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

web_search = TavilySearchResults(max_results=2)

# 定义模型
model = ChatOpenAI(
    model_name="gpt-5-mini",
    openai_api_key=OPENAI_API_KEY
)

@tool
def get_weather(loc):
    """
    查询即时天气函数
    :param loc: 必要参数，字符串类型，用于表示查询天气的具体城市名称，\
    注意，中国的城市需要用对应城市的英文名称代替，例如如果需要查询北京市天气，则loc参数需要输入'Beijing'；
    :return：OpenWeather API查询即时天气的结果，具体URL请求地址为：https://api.openweathermap.org/data/2.5/weather\
    返回结果对象类型为解析之后的JSON格式对象，并用字符串形式进行表示，其中包含了全部重要的天气信息
    """
    # Step 1.构建请求
    url = "https://api.weatherapi.com/v1/current.json"
    params = {
        "q": loc,
        "key": os.getenv("OPENWEATHER_API_KEY"),
    }

    # Step 3.发送GET请求
    response = requests.get(url, params=params)

    # Step 4.解析响应
    data = response.json()
    return json.dumps(data)

# 创建Agent
prompt = """
你是一名乐于助人的智能助手，擅长根据用户的问题选择合适的工具来查询信息并回答。

当用户的问题涉及**天气信息**时，你应优先调用`get_weather`工具，查询用户指定城市的实时天气，并在回答中总结查询结果。

当用户的问题涉及**新闻、事件、实时动态**时，你应优先调用`web_search`工具，检索相关的最新信息，并在回答中简要概述。

如果问题既包含天气又包含新闻，请先使用`get_weather`查询天气，再使用`web_search`查询新闻，最后将结果合并后回复用户。

重要：请记住对话历史中的信息，包括用户的名字、偏好和其他重要信息，以便在后续对话中提供更加个性化的服务。
"""

# 初始化checkpoint和记忆存储
# checkpointer = MemorySaver()

agent = create_agent(
    model=model,
    tools=[get_weather, web_search],
    system_prompt=prompt,
    # checkpointer=checkpointer
)