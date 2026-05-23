from dotenv import load_dotenv

load_dotenv()

import asyncio

from .agent import Agent, AgentConfiguration, AgentInput, create_llm
from .tools import MCPRuntime


async def main():
    runtime = MCPRuntime()

    try:
        tools = await runtime.start()

        print("Loaded tools:")
        for i, tool in enumerate(tools):
            print(i, tool.name)

        llm = create_llm()

        config = AgentConfiguration(tools=tools)
        agent = Agent(llm, config)

        agent_input = AgentInput(
            user_input="What's the current time, calculate 15 * 23?"
        )

        session = agent.run(agent_input)

        print("Starting agent execution...")

        while True:
            result = await session.step()

            if result.stage is None:
                print("Execution complete!")
                break

            print(f"Stage: {result.stage}")

            if result.content:
                print(f"Content: {result.content}")

            print("-" * 50)

    finally:
        await runtime.close()


if __name__ == "__main__":
    asyncio.run(main())