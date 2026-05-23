import json
import re
import ast
import uuid
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.agent import Agent, create_llm, list_tools, AgentInput, AgentConfiguration


class AgentCreate(BaseModel):
    name: str
    system_prompt: str
    model_provider: str
    model_name: str
    allowed_tools: List[str]
    max_steps: int
    forbidden_topics: List[str]


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    system_prompt: Optional[str] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    allowed_tools: Optional[List[str]] = None
    max_steps: Optional[int] = None
    forbidden_topics: Optional[List[str]] = None


class AgentOut(AgentCreate):
    id: str


class RunRequest(BaseModel):
    user_input: str


class RunOut(BaseModel):
    id: str
    agent_id: str
    status: str
    final_answer: Optional[str] = ""


class EventOut(BaseModel):
    id: str
    run_id: str
    step: int
    type: str
    title: str
    payload: Optional[str] = None


class AgentItem:
    def __init__(self, agent_out: AgentOut, agent: Agent):
        self.agent_out = agent_out
        self.agent = agent


agents_db: dict[str, AgentItem] = {}
runs_db: dict[str, RunOut] = {}
events_db: dict[str, List[EventOut]] = {}
llm = create_llm()


async def run_agent(agent: Agent, user_input: str) -> tuple[str, str, List[EventOut]]:
    config = AgentConfiguration(tools=["search_web", "calculate", "get_current_time"])
    agent = Agent(llm, config)
    agent_input = AgentInput(user_input=user_input)

    session = agent.run(agent_input)

    events = [
        EventOut(
            id=str(uuid.uuid4()),
            run_id="",
            step=1,
            type="user_input",
            title="User Input",
            payload=user_input,
        ),
    ]
    final_answer = ""

    step_id = 2
    while True:
        result = await session.step()
        if result.stage is None:
            break
        events.append(
            EventOut(
                id=str(uuid.uuid4()),
                run_id="",
                step=step_id,
                type=result.stage,
                title=result.stage,
                payload=result.content,
            )
        )
        final_answer = result.content
        # assert result.content
        step_id += 1

    return "completed", final_answer, events


# ── API Router ────────────────────────────────────────────────────────────────

router = APIRouter()


class ToolResponse(BaseModel):
    tool_name: str


@router.get("/tools", response_model=List[ToolResponse])
async def list_tools_api():
    return [ToolResponse(tool_name=tool) for tool in list_tools()]


@router.get("/agents", response_model=List[AgentOut])
async def list_agents():
    return [v.agent_out for _, v in agents_db.items()]


@router.post("/agents", response_model=AgentOut, status_code=201)
async def create_agent(agent: AgentCreate):
    agent_id = str(uuid.uuid4())
    new_agent = AgentOut(id=agent_id, **agent.dict())
    config = AgentConfiguration(
        tools=agent.allowed_tools, system_prompt=agent.system_prompt
    )
    agents_db[agent_id] = AgentItem(new_agent, Agent(llm, config))
    return new_agent


@router.put("/agents/{agent_id}", response_model=AgentOut)
async def update_agent(agent_id: str, updates: AgentUpdate):
    raise NotImplementedError
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent = agents_db[agent_id]
    update_data = updates.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(agent, key, value)
    agents_db[agent_id] = agent
    return agent


@router.post("/agents/{agent_id}/runs", response_model=RunOut)
async def create_run(agent_id: str, run_req: RunRequest):
    agent = agents_db.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent = agent.agent

    run_id = str(uuid.uuid4())
    status, final_answer, ev_list = await run_agent(agent, run_req.user_input)

    for ev in ev_list:
        ev.run_id = run_id
    events_db[run_id] = ev_list

    run = RunOut(id=run_id, agent_id=agent_id, status=status, final_answer=final_answer)
    runs_db[run_id] = run
    return run


@router.get("/runs/{run_id}/events", response_model=List[EventOut])
async def get_events(run_id: str):
    if run_id not in events_db:
        raise HTTPException(status_code=404, detail="Run not found")
    return events_db[run_id]


app = FastAPI(title="Agentic Studio Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
