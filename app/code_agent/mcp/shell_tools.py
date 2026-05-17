import shlex
import subprocess
from typing import Annotated

from langsmith import traceable
from mcp.server.fastmcp import FastMCP
from pydantic.fields import Field

mcp = FastMCP()

@traceable(run_type="tool", name="Run Shell Command")
@mcp.tool(name="run_shell", description="Run a shell command")
def run_shell_command(command: 
                      Annotated[str, Field(description="shell command will be executed", 
                                           json_schema_extra={
                                                "example": "ls -la"
                                            })]) -> str:
    try:
        shell_command = shlex.split(command)
        if "rm " in shell_command:
            raise Exception("rm command is not allowed for security reasons.")
        
        res = subprocess.run(command, shell=True, capture_output=True, text=True)

        if res.returncode != 0:
            return res.stderr
        return res.stdout
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    mcp.run(transport="stdio")