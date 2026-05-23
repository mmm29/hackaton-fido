from dataclasses import dataclass
from typing import Any

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field, ConfigDict


class Llm:
    async def invoke(self, messages: list[BaseMessage]):
        raise NotImplementedError


@dataclass
class AgentInput:
    user_input: str


@dataclass
class AgentStepResult:
    stage: str | None
    data: dict | None = None


class AgentState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    user_input: str
    selected_tool: str | None = None
    tool_args: dict[str, Any] = Field(default_factory=dict)
    tool_result: Any | None = None
    answer: str | None = None


def make_plan_node(llm: Llm):
    async def plan_node(state: AgentState) -> dict:
        text = state.user_input.lower()

        if "час" in text or "time" in text:
            return {
                "selected_tool": "get_current_time",
                "tool_args": {},
            }

        if "аналіз" in text or "графік" in text or "поліном" in text:
            return {
                "selected_tool": "analyze_and_plot_points",
                "tool_args": {
                    "points": [[1, 2], [2, 4.1], [3, 6.2], [4, 8.1], [5, 10.3]],
                    "degree": 1,
                },
            }

        return {
            "answer": "Поки агент не зрозумів, який інструмент потрібно викликати."
        }

    return plan_node


def make_tool_node(tools: list):
    tools_by_name = {tool.name: tool for tool in tools}

    async def tool_node(state: AgentState) -> dict:
        if state.selected_tool is None:
            return {}

        tool = tools_by_name.get(state.selected_tool)

        if tool is None:
            return {
                "tool_result": {
                    "error": f"Tool '{state.selected_tool}' not found."
                }
            }

        result = await tool.ainvoke(state.tool_args)

        return {
            "tool_result": result,
        }

    return tool_node


def make_answer_node():
    async def answer_node(state: AgentState) -> dict:
        if state.answer is not None:
            return {
                "answer": state.answer,
            }

        return {
            "answer": f"Результат виконання tool '{state.selected_tool}': {state.tool_result}"
        }

    return answer_node


def route_after_plan(state: AgentState) -> str:
    if state.selected_tool is not None:
        return "tools"

    return "answer"


class AgentSession:
    def __init__(self, llm: Llm, config: "AgentConfiguration", agent_input: AgentInput) -> None:
        self.llm = llm
        self.config = config

        graph = StateGraph(AgentState)

        graph.add_node("plan", make_plan_node(llm))
        graph.add_node("tools", make_tool_node(config.tools))
        graph.add_node("answer", make_answer_node())

        graph.set_entry_point("plan")

        graph.add_conditional_edges(
            "plan",
            route_after_plan,
            {
                "tools": "tools",
                "answer": "answer",
            },
        )

        graph.add_edge("tools", "answer")
        graph.add_edge("answer", END)

        self.app = graph.compile()

        initial_state = AgentState(user_input=agent_input.user_input)
        self.steps = self.app.astream(initial_state)

    async def step(self) -> AgentStepResult:
        try:
            res = await anext(self.steps)
            stage = next(iter(res.keys())) if res else None

            return AgentStepResult(
                stage=stage,
                data=res,
            )

        except StopAsyncIteration:
            return AgentStepResult(
                stage=None,
                data={"done": True},
            )


@dataclass
class AgentConfiguration:
    tools: list


class Agent:
    def __init__(self, llm: Llm, config: AgentConfiguration) -> None:
        self.llm = llm
        self.config = config

    def run(self, agent_input: AgentInput) -> AgentSession:
        return AgentSession(self.llm, self.config, agent_input)