import os
from datetime import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("WriteServer")
USER_AGENT = "write-app/1.0"

OUTPUT_DIR = "./output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

@mcp.tool()
async def write_to_file(content: str) -> str:
    """
    将内容写入指定文件
    :param content: 要写入的内容
    :return: 写入成功的结果和文件路径
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"note_{timestamp}.txt"
    filepath = os.path.join(OUTPUT_DIR, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(content)
        return f"内容已成功写入文件: {filepath}"
    except Exception as e:
        return f"写入文件时出错: {e}"

if __name__ == "__main__":
    mcp.run(transport='stdio') 