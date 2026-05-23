import asyncio

from .agent import Agent, Llm, AgentConfiguration, AgentInput
from .tools import load_mcp_tools


async def main():
    tools = await load_mcp_tools()
    print(tools)
    llm = Llm()
    config = AgentConfiguration(tools=["tool1", "tool2"])
    agent = Agent(llm, config)
    session = agent.run(AgentInput(user_input="hello"))
    for _ in range(10):
        print("epoch", await session.step())


if __name__ == "__main__":
    asyncio.run(main())
