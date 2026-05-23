from dataclasses import dataclass

from langgraph.graph import StateGraph
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from pydantic import BaseModel


class Llm:
    def invoke(self, messages: list[BaseMessage]):
        raise NotImplementedError


class Tool:
    pass


@dataclass
class AgentInput:
    user_input: str


@dataclass
class AgentStepResult:
    stage: str | None


class AgentState(BaseModel):
    user_input: str


# TODO: todo
PLANNER_SYSTEM = None


def make_plan_node(llm: Llm):
    async def plan_node(state: AgentState) -> dict:
        # resp = await llm.invoke(
        #     [
        #         SystemMessage(content=PLANNER_SYSTEM),
        #         HumanMessage(content=state.user_input),
        #     ]
        # )

        return {
            # "plan": resp.content if hasattr(resp, "content") else str(resp),
            # "phase": "research",
            # "messages": [
            #     SystemMessage(content=RESEARCH_SYSTEM),
            #     HumanMessage(content=f"User message:\n{q}\n\nPlan:\n{resp.content}"),
            # ],
        }

    return plan_node


def make_tool_node():
    raise NotImplementedError


def make_agent_node():
    async def agent_node(state: AgentState) -> dict:
        return {}

    return agent_node


def make_validate_node():
    async def validation_node(state: AgentState) -> dict:
        return {}

    return validation_node


def make_answer_node():
    async def answer_node(state: AgentState) -> dict:
        return {}

    return answer_node


class AgentSession:
    def __init__(self, llm: Llm, agent_input: AgentInput) -> None:
        self.llm = llm

        graph = StateGraph(AgentState)

        graph.add_node("plan", make_plan_node(llm))
        graph.add_node("agent", make_agent_node())
        # graph.add_node("tools", make_tool_node())
        # graph.add_node("validate", make_validate_node())
        graph.add_node("answer", make_answer_node())

        graph.set_entry_point("plan")
        graph.add_edge("plan", "agent")
        graph.add_edge("agent", "answer")

        self.app = graph.compile()
        initial_state = AgentState(user_input=agent_input.user_input)
        self.steps = self.app.astream(initial_state)

    async def step(self) -> AgentStepResult:
        try:
            res = await anext(self.steps)
            print(res)
            return 0
        except StopAsyncIteration:
            return 0


@dataclass
class AgentConfiguration:
    tools: list[str]


class Agent:
    def __init__(self, llm: Llm, config: AgentConfiguration) -> None:
        self.llm = llm
        self.config = config

    def run(self, agent_input: AgentInput) -> AgentSession:
        return AgentSession(self.llm, agent_input)
