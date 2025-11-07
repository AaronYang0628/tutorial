import asyncio

from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

# 为 stdio 连接创建服务器参数
server_params = StdioServerParameters(
    command='uv',
    args=['run', 'report_weather.py'],
)


async def main():
    # 创建 stdio 客户端
    async with stdio_client(server_params) as (stdio, write):
        # 创建 ClientSession 对象
        async with ClientSession(stdio, write) as session:
            # 初始化 ClientSession
            await session.initialize()

            # 列出可用的工具
            response = await session.list_tools()
            print(response)

            # 调用工具
            response = await session.call_tool('fetch_weather_in', {'city': '杭州', 'days': 2})
            print(response)


if __name__ == '__main__':
    asyncio.run(main())
