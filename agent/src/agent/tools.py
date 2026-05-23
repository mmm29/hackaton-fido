from pathlib import Path
import sys

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools as load_tools_from_session


class MCPRuntime:
    def __init__(self) -> None:
        self.client: MultiServerMCPClient | None = None
        self.session_cm = None
        self.session = None
        self.tools: list | None = None

    async def start(self) -> list:
        if self.tools is not None:
            return self.tools

        projroot = Path(__file__).resolve().parents[3]
        tools_script_path = projroot / "mcp" / "mcp_server.py"

        self.client = MultiServerMCPClient(
            {
                "mcp-tools": {
                    "command": sys.executable,
                    "args": [str(tools_script_path)],
                    "transport": "stdio",
                    "cwd": str(projroot),
                },
            }
        )

        self.session_cm = self.client.session("mcp-tools")
        self.session = await self.session_cm.__aenter__()

        self.tools = await load_tools_from_session(self.session)
        return self.tools

    async def close(self) -> None:
        if self.session_cm is not None:
            await self.session_cm.__aexit__(None, None, None)

        self.session_cm = None
        self.session = None
        self.client = None
        self.tools = None


def get_tool_by_name(tools: list, name: str):
    for tool in tools:
        if tool.name == name:
            return tool

    raise ValueError(f"Tool '{name}' not found.")