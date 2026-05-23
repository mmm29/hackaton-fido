from pathlib import Path
import sys

from langchain_mcp_adapters.client import MultiServerMCPClient


async def load_mcp_tools() -> list:
    projroot = Path(__file__).resolve().parents[3]
    tools_script_path = projroot / "mcp" / "mcp_server.py"

    client = MultiServerMCPClient(
        {
            "mcp-tools": {
                "command": sys.executable,
                "args": [str(tools_script_path)],
                "transport": "stdio",
                "cwd": str(projroot),
            },
        }
    )

    return await client.get_tools()
