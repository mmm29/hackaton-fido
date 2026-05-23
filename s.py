import asyncio
import time

from agent.src.agent.tools import MCPRuntime, get_tool_by_name


async def main():
    runtime = MCPRuntime()

    try:
        t0 = time.perf_counter()
        tools = await runtime.start()
        t1 = time.perf_counter()

        print(f"runtime.start: {t1 - t0:.3f} sec")

        for i, tool in enumerate(tools):
            print(i, tool.name)

        tool = get_tool_by_name(tools, "get_current_time")

        for i in range(5):
            t2 = time.perf_counter()
            result = await tool.ainvoke({})
            t3 = time.perf_counter()

            print(f"invoke {i + 1}: {t3 - t2:.3f} sec -> {result}")

    finally:
        await runtime.close()


asyncio.run(main())