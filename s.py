import asyncio

from agent.tools import load_mcp_tools


async def main():
    tools = await load_mcp_tools()
    print(await tools[1].ainvoke({}))


asyncio.run(main())
