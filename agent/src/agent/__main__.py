import asyncio

from .agent import Agent, Llm, AgentConfiguration, AgentInput
from .tools import load_mcp_tools


async def main():
    tools = await load_mcp_tools()

    for i, tool in enumerate(tools):
        print(i, tool.name)

    llm = Llm()

    config = AgentConfiguration(tools=tools)
    agent = Agent(llm, config)

    session = agent.run(
        AgentInput(user_input="Покажи поточний час")
    )

    while True:
        step = await session.step()

        print("stage:", step.stage)
        print("data:", step.data)

        if step.stage is None:
            break


if __name__ == "__main__":
    asyncio.run(main())