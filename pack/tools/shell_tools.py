import asyncio
import shlex
from typing import Any, Dict, List, Optional

from ..tool import Tool


def create_shell_tools() -> List[Tool]:

    async def _shell(**kwargs: Any) -> str:
        command: str = kwargs["command"]
        timeout: Optional[float] = kwargs.get("timeout", 60.0)
        cwd: Optional[str] = kwargs.get("cwd")

        # Safety: reject obviously dangerous commands
        dangerous = ["rm -rf /", "rm -rf /*", "> /dev/sda"]
        stripped = command.strip()
        for d in dangerous:
            if d in stripped:
                return f"Error: dangerous command blocked: {d!r}"

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            stdout_data, stderr_data = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            if proc.returncode is None:
                try:
                    proc.kill()
                    await proc.wait()
                except Exception:
                    pass
            return f"Error: command timed out after {timeout} seconds"
        except Exception as exc:
            return f"Error: {exc}"

        stdout_text = stdout_data.decode("utf-8", errors="replace") if stdout_data else ""
        stderr_text = stderr_data.decode("utf-8", errors="replace") if stderr_data else ""

        lines: List[str] = []
        if stdout_text:
            lines.append("[stdout]\n" + stdout_text)
        if stderr_text:
            lines.append("[stderr]\n" + stderr_text)
        if proc.returncode != 0:
            lines.append(f"[exit code] {proc.returncode}")

        return "\n".join(lines) if lines else "(no output)"

    return [
        Tool(
            name="shell",
            description=(
                "Execute a shell command and return stdout, stderr, and exit code. "
                "Use with caution: avoid destructive or irreversible operations."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute.",
                    },
                    "timeout": {
                        "type": "number",
                        "minimum": 1.0,
                        "maximum": 300.0,
                        "default": 60.0,
                        "description": "Maximum execution time in seconds (1-300).",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Optional working directory for the command.",
                    },
                },
                "required": ["command"],
            },
            handler=_shell,
        ),
    ]
