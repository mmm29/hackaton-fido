from dotenv import load_dotenv

load_dotenv()

import asyncio

from .agent import Agent, Llm, AgentConfiguration, AgentInput, create_llm
from .tools import load_mcp_tools


# Example usage
async def main():
    llm = create_llm()

    config = AgentConfiguration(tools=["search_web", "calculate", "get_current_time"])
    agent = Agent(llm, config)

    agent_input = AgentInput(user_input="What's the current time, calculate 15 * 23?")

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


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
