from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import os
from dotenv import load_dotenv

load_dotenv()

# Construct server URL with authentication
from urllib.parse import urlencode
base_url = "https://server.smithery.ai/@smithery/notion/mcp"
params = {"api_key": os.getenv("SMITHERY_API_KEY"), "profile": os.getenv("SMITHERY_PROFILE")}
url = f"{base_url}?{urlencode(params)}"

# Available tools
async def main():
    # Connect to the server using HTTP client
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            # List available tools
            tools_result = await session.list_tools()
            print(f"Available tools: {', '.join([t.name for t in tools_result.tools])}")

# list-databases
async def list_databases():
    # 서버에 연결합니다.
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 사용 가능한 툴을 나열합니다. (기존 코드)
            tools_result = await session.list_tools()
            print(f"사용 가능한 툴: {', '.join([t.name for t in tools_result.tools])}\n")

            # --- 'notion_list_databases' 툴을 사용하는 예시입니다. ---
            try:
                print("노션 데이터베이스 목록을 가져오는 중...\n")
                
                # 'notion_list_databases' 툴을 호출합니다.
                list_result = await session.call_tool(
                    name="list-databases",
                    arguments={}# 이 툴은 특별한 인자가 필요하지 않습니다.
                )
                
                # 결과 출력
                print("✅ 성공!")
                print("--- 발견된 데이터베이스 목록 ---")
                
                print(list_result.structuredContent.get("databases"))
            
            except Exception as e:
                print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(list_databases())