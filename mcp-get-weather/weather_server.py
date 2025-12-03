import os 
import json
import httpx
from typing import Any
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP 


mcp = FastMCP("WeatherServer")
USER_AGENT = "weather-app/1.0"

load_dotenv(override=True)
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

async def get_weather(loc):
    """
    查询即时天气函数
    :param loc: 必要参数，字符串类型，用于表示查询天气的具体城市名称，\
    注意，中国的城市需要用对应城市的英文名称代替，例如如果需要查询北京市天气，则loc参数需要输入'Beijing'；
    :return：OpenWeather API查询即时天气的结果，具体URL请求地址为：https://api.openweathermap.org/data/2.5/weather\
    返回结果对象类型为解析之后的JSON格式对象，并用字符串形式进行表示，其中包含了全部重要的天气信息
    """
    print("API KEY:" + OPENWEATHER_API_KEY)
    # Step 1.构建请求
    url = "https://api.weatherapi.com/v1/current.json"

    # Step 2.设置查询参数
    params = {
        "q": loc,
        "key": OPENWEATHER_API_KEY,    # 输入API key
        "aqi": "no",        
    }

    headers = {"User-Agent": USER_AGENT}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            weather_data = response.json()
            return weather_data
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            return {"error": "HTTP error occurred while fetching weather data."}
        except Exception as e:
            print(f"An error occurred: {e}")
            return {"error": "An unexpected error occurred while fetching weather data."}

def format_weather(data: Any) -> str:
    """
    格式化天气查询结果
    :param data: WeatherAPI返回的天气数据对象（字典或字符串）
    :return: 格式化后的字符串，包含主要天气信息
    """
    # 处理字符串输入
    if isinstance(data, str):
        try:
            weather_data = json.loads(data)
        except json.JSONDecodeError:
            return "无法解析天气数据。"
    # 处理字典输入
    elif isinstance(data, dict):
        weather_data = data
    else:
        return "无效的天气数据格式。"

    # 检查是否有错误信息
    if "error" in weather_data:
        return weather_data.get("error", "获取天气数据时发生错误。")

    # 正确访问 weatherapi.com 的嵌套数据结构
    location = weather_data.get("location", {})
    current = weather_data.get("current", {})

    city = location.get("name", "未知城市")
    region = location.get("region", "")
    country = location.get("country", "")
    temp_c = current.get("temp_c", "未知")
    condition = current.get("condition", {}).get("text", "未知")
    humidity = current.get("humidity", "未知")
    wind_kph = current.get("wind_kph", "未知")

    formatted_response = (
        f"当前天气信息：\n"
        f"城市: {city}, {region}, {country}\n"
        f"温度: {temp_c}°C\n"
        f"天气状况: {condition}\n"
        f"湿度: {humidity}%\n"
        f"风速: {wind_kph} kph\n"
    )

    return formatted_response

@mcp.tool()
async def query_weather(location: str) -> str:
    """
    查询指定城市的即时天气信息
    :param location: 必要参数，字符串类型，用于表示查询天气的具体城市名称，\
    注意，中国的城市需要用对应城市的英文名称代替，例如如果需要查询北京市天气，则location参数需要输入'Beijing'；
    :return 格式化后的字符串，包含主要天气信息
    """
    weather_data = await get_weather(location)
    formatted_weather = format_weather(weather_data)
    return formatted_weather

if __name__ == "__main__":
    mcp.run(transport="stdio")