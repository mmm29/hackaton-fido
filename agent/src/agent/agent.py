from dataclasses import dataclass
import os
from typing import Literal
import asyncio

from langgraph.graph import StateGraph, END
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    BaseMessage,
    ToolMessage,
)

from langchain_openai import ChatOpenAI

from langchain_core.tools import tool
from pydantic import BaseModel


class Llm:
    def __init__(self, llm):
        self.llm = llm

    async def invoke(self, messages: list[BaseMessage]):
        return await self.llm.ainvoke(messages)

    def bind_tools(self, tools: list):
        return Llm(self.llm.bind_tools(tools))


def create_llm():
    base_url = os.environ["OPENAI_BASE_URL"]
    api_key = os.environ["OPENAI_API_KEY"]
    model_id = os.environ["OPENAI_MODEL_ID"]

    # return Llm(ChatGoogleGenerativeAI(model=model_id, api_key=api_key))
    return Llm(ChatOpenAI(model=model_id, api_key=api_key, base_url=base_url))


@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 2", "15 * 3")
    """
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"Result: {expression} = {result}"
    except Exception as e:
        return f"Error calculating: {str(e)}"


@tool
def get_current_time() -> str:
    """Get the current date and time."""
    from datetime import datetime

    return f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"


# Tool registry
TOOLS = {
    "calculate": calculate,
    "get_current_time": get_current_time,
}


class Tool:
    def __init__(self, tool_func):
        self.func = tool_func
        self.name = tool_func.name
        self.description = tool_func.description

    async def run(self, **kwargs):
        return self.func.run(**kwargs)


@dataclass
class AgentInput:
    user_input: str


@dataclass
class AgentStepResult:
    stage: str | None = None
    content: str | None = None
    raw_content: dict | None = None


class AgentState(BaseModel):
    messages: list[BaseMessage] = []
    plan: str | None = None
    tool_calls: list[dict] = []
    content: str | None = None
    tool_results: list[dict] = []
    final_answer: str | None = None


PLANNER_SYSTEM = """You are an expert planning agent. Your role is to create a clear, step-by-step plan to solve the user's query.

When creating a plan:
1. Break down the task into logical steps
2. Identify what tools or information might be needed
3. Consider dependencies between steps
4. Keep plans concise but comprehensive

Respond with a numbered list of steps. Each step should be clear and actionable."""

RESEARCH_SYSTEM = """You are a helpful research assistant with access to various tools.
You can call multiple tools simultaneously when the operations are independent of each other.

Always:
- Use tools when you need external information
- Call multiple tools at once when they don't depend on each other
- Explain your reasoning clearly
- Verify information before providing final answers"""

VALIDATION_SYSTEM = """You are a validation agent. Your role is to verify that the agent's response:
1. Addresses all parts of the user's query
2. Is accurate based on the tool results provided
3. Contains no hallucinations or unsupported claims
4. Is clear and well-structured

Respond with either:
- "PASS" if the response is satisfactory
- "FAIL: [reason]" if improvements are needed"""


def make_plan_node(llm: Llm):
    async def plan_node(state: AgentState) -> dict:
        user_query = state.messages[-1].content if state.messages else ""

        resp = await llm.invoke(
            [
                SystemMessage(content=PLANNER_SYSTEM),
                HumanMessage(content=f"Create a plan for this query: {user_query}"),
            ]
        )

        plan = resp.content if hasattr(resp, "content") else str(resp)

        return {
            "plan": plan,
            "messages": state.messages + [AIMessage(content=f"Plan created:\n{plan}")],
            "content": plan,
        }

    return plan_node


def make_tool_calling_agent_node(llm: Llm, tools: list):
    tool_calling_llm = llm.bind_tools(tools)

    async def agent_node(state: AgentState) -> dict:
        messages = state.messages + [SystemMessage(content=RESEARCH_SYSTEM)]

        resp = await tool_calling_llm.invoke(messages)

        if hasattr(resp, "tool_calls") and resp.tool_calls:
            return {
                "messages": state.messages + [resp],
                "tool_calls": resp.tool_calls,
                "content": "Calling tools..",
            }

        return {
            "messages": state.messages + [resp],
            "final_answer": resp.content,
            "content": resp.content,
        }

    return agent_node


def make_tool_execution_node(tool_registry: dict):
    async def tool_node(state: AgentState) -> dict:
        tool_calls = state.tool_calls
        tool_results = []
        new_messages = state.messages.copy()

        async def execute_single_tool(tool_call):
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})
            tool_id = tool_call.get("id")

            tool_func = tool_registry.get(tool_name)
            if tool_func:
                try:
                    if hasattr(tool_func, "ainvoke"):
                        result = await tool_func.ainvoke(tool_args)
                    elif hasattr(tool_func, "invoke"):
                        result = tool_func.invoke(tool_args)
                    else:
                        result = tool_func(**tool_args)

                    return {
                        "tool_call_id": tool_id,
                        "tool_name": tool_name,
                        "result": str(result),
                    }
                except Exception as e:
                    return {
                        "tool_call_id": tool_id,
                        "tool_name": tool_name,
                        "error": str(e),
                    }
            else:
                return {
                    "tool_call_id": tool_id,
                    "tool_name": tool_name,
                    "error": f"Tool {tool_name} not found",
                }

        tasks = [execute_single_tool(tc) for tc in tool_calls]
        results = await asyncio.gather(*tasks)

        # Create tool messages
        for result in results:
            tool_msg = ToolMessage(
                content=result.get("result", result.get("error", "")),
                tool_call_id=result["tool_call_id"],
            )
            new_messages.append(tool_msg)
            tool_results.append(result)

        return {
            "messages": new_messages,
            "tool_results": tool_results,
            "tool_calls": [],  # Clear tool calls after execution
            "content": "Tools called.",
        }

    return tool_node


def make_validate_node(llm: Llm):
    async def validation_node(state: AgentState) -> dict:
        if not state.final_answer:
            return {"messages": state.messages}

        messages = [
            SystemMessage(content=VALIDATION_SYSTEM),
            HumanMessage(
                content=f"""
User query: {state.messages[0].content if state.messages else "N/A"}
Plan: {state.plan}
Final answer: {state.final_answer}
Tool results: {state.tool_results}

Please validate this response."""
            ),
        ]

        resp = await llm.invoke(messages)
        validation_result = resp.content if hasattr(resp, "content") else str(resp)

        if "PASS" in validation_result:
            return {
                "messages": state.messages + [AIMessage(content="Validation passed ✓")],
                "content": "Validation passed",
            }
        else:
            return {
                "messages": state.messages
                + [
                    AIMessage(
                        content=f"Validation failed. Feedback: {validation_result}"
                    ),
                    HumanMessage(
                        content=f"Please improve your answer based on this feedback: {validation_result}"
                    ),
                ],
                "final_answer": None,
                "content": "Validation failed",
            }

    return validation_node


def make_answer_node():
    async def answer_node(state: AgentState) -> dict:
        if state.final_answer:
            formatted_answer = f"Answer: {state.final_answer}"
        else:
            formatted_answer = "I couldn't generate a proper answer."

        return {
            "messages": state.messages + [AIMessage(content=formatted_answer)],
            "final_answer": formatted_answer,
            "content": formatted_answer,
        }

    return answer_node


def should_continue(state: AgentState) -> Literal["tools", "validate", "answer"]:
    if state.tool_calls:
        return "tools"
    elif state.final_answer:
        return "validate"
    else:
        return "answer"


def should_retry(state: AgentState) -> Literal["agent", "answer"]:
    if state.final_answer is None:
        return "agent"
    else:
        return "answer"


class AgentSession:
    def __init__(self, llm: Llm, agent_input: AgentInput, tools: list) -> None:
        tool_registry = {tool.name: tool for tool in tools}

        graph = StateGraph(AgentState)

        graph.add_node("plan", make_plan_node(llm))
        graph.add_node("agent", make_tool_calling_agent_node(llm, tools))
        graph.add_node("tools", make_tool_execution_node(tool_registry))
        graph.add_node("validate", make_validate_node(llm))
        graph.add_node("answer", make_answer_node())

        graph.set_entry_point("plan")
        graph.add_edge("plan", "agent")

        graph.add_conditional_edges(
            "agent",
            should_continue,
            {"tools": "tools", "validate": "validate", "answer": "answer"},
        )

        graph.add_edge("tools", "agent")
        graph.add_conditional_edges(
            "validate", should_retry, {"agent": "agent", "answer": "answer"}
        )
        graph.add_edge("answer", END)

        self.app = graph.compile()
        initial_state = AgentState(
            messages=[HumanMessage(content=agent_input.user_input)]
        )
        self.steps = self.app.astream(initial_state)

    async def step(self) -> AgentStepResult:
        try:
            res = await anext(self.steps)
            node_name = list(res.keys())[0] if res else None
            dat = res[node_name]
            return AgentStepResult(
                stage=node_name, raw_content=res, content=dat["content"]
            )
        except StopAsyncIteration:
            return AgentStepResult()


@dataclass
class AgentConfiguration:
    tools: list


class Agent:
    def __init__(self, llm: Llm, config: AgentConfiguration) -> None:
        self.llm = llm
        self.config = config

    def run(self, agent_input: AgentInput) -> AgentSession:
        return AgentSession(self.llm, agent_input, self.config.tools)
