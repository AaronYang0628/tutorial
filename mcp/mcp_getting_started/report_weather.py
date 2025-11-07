from typing import Dict, Any
import httpx
from mcp.server import FastMCP
from mcp.types import LoggingLevel
from dotenv import load_dotenv


load_dotenv()

# 初始化 FastMCP 服务器
app = FastMCP('report-weather')

async def log_info(message: str):
    """发送 INFO 级别日志到 MCP Inspector"""
    try:
        context = app.request_context
        if context and hasattr(context, 'session'):
            await context.session.send_log_message(
                level=LoggingLevel.INFO,
                data=message
            )
    except:
        pass

async def log_error(message: str):
    """发送 ERROR 级别日志到 MCP Inspector"""
    try:
        context = app.request_context
        if context and hasattr(context, 'session'):
            await context.session.send_log_message(
                level=LoggingLevel.ERROR,
                data=message
            )
    except:
        pass
@app.tool()
async def fetch_weather_in(city: str, days: int = 0) -> Dict[str, Any]:
    """
    通过调用 wttr.in API 查询天气信息。
    
    Args:
        city: 城市名称
        days: 预报天数，0表示当天
        
    Returns:
        Dict[str, Any]: 包含天气信息的字典
    """
    # API端点，请求JSON格式的数据
    url = f"https://wttr.in/{city}+{days}?format=j1"
    
    async with httpx.AsyncClient() as client:
        try:
            # 发起异步网络请求
            response = await client.get(url)
            response.raise_for_status()
            # 解析返回的JSON数据
            data = response.json()
        
            await log_info(f"成功获取 {city} 的天气数据 {data}")
            # 提取当前天气状况
            current_condition = data['current_condition'][0]
            weather_desc = current_condition['weatherDesc'][0]['value']
            temp_c = current_condition['temp_C']
        
            # 格式化成自然语言返回
            # 格式化天气信息
            weather_info = {
                "current": {
                    "city": city,
                    "temperature": data['current_condition'][0]['temp_C'],
                    "description": data['current_condition'][0]['weatherDesc'][0]['value'],
                    "humidity": data['current_condition'][0]['humidity'],
                    "feels_like": data['current_condition'][0]['FeelsLikeC']
                }
            }

            return weather_info
            
        except httpx.RequestError as e:
            raise Exception(f"网络请求错误: {str(e)}")
        except (KeyError, IndexError) as e:
            raise Exception(f"解析天气数据失败，城市名称可能无效: {str(e)}")
        except Exception as e:
            raise Exception(f"获取天气信息时发生错误: {str(e)}")

if __name__ == "__main__":
    # 在开发环境中运行MCP服务器
    app.run(transport='stdio')