"""Shell command execution tool."""

import asyncio
import os
import signal
import sys
from pathlib import Path

from pydantic import BaseModel, Field

from notebooks.agent.tools.base import Tool, ToolConfirmation, ToolInvocation, ToolKind, ToolResult


BLOCKED_COMMANDS = {
    "rm -rf /", "rm -rf ~", "rm -rf /*",
    "dd if=/dev/zero", "dd if=/dev/random",
    "mkfs", "fdisk", ":(){ :|:& };:",
    "chmod 777 /", "chmod -R 777",
    "shutdown", "reboot", "halt", "poweroff",
}


class ShellParams(BaseModel):
    command: str = Field(..., description="The shell command to execute")
    timeout: int = Field(120, ge=1, le=600, description="Timeout in seconds")
    cwd: str | None = Field(None, description="Working directory for the command")


class ShellTool(Tool):
    name = "shell"
    kind = ToolKind.SHELL
    description = "Execute a shell command. Use for running system commands, scripts, and CLI tools."
    schema = ShellParams

    async def get_confirmation(self, invocation: ToolInvocation) -> ToolConfirmation | None:
        params = ShellParams(**invocation.params)
        is_dangerous = any(b in params.command for b in BLOCKED_COMMANDS)
        return ToolConfirmation(
            tool_name=self.name,
            params=invocation.params,
            description=f"Execute: {params.command}",
            command=params.command,
            is_dangerous=is_dangerous,
        )

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = ShellParams(**invocation.params)

        cmd_lower = params.command.lower().strip()
        for blocked in BLOCKED_COMMANDS:
            if blocked in cmd_lower:
                return ToolResult.error_result(
                    f"Command blocked for safety: {params.command}",
                    metadata={"blocked": True},
                )

        cwd = invocation.cwd
        if params.cwd:
            p = Path(params.cwd)
            cwd = p if p.is_absolute() else (invocation.cwd / p)

        if not cwd.exists():
            return ToolResult.error_result(f"Working directory doesn't exist: {cwd}")

        env = self._build_environment()

        if sys.platform == "win32":
            shell_cmd = ["cmd.exe", "/c", params.command]
        else:
            shell_cmd = ["/bin/bash", "-c", params.command]

        process = await asyncio.create_subprocess_exec(
            *shell_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
            start_new_session=True,
        )

        try:
            stdout_data, stderr_data = await asyncio.wait_for(
                process.communicate(), timeout=params.timeout,
            )
        except asyncio.TimeoutError:
            if sys.platform != "win32":
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            else:
                process.kill()
            await process.wait()
            return ToolResult.error_result(f"Command timed out after {params.timeout}s")

        stdout = stdout_data.decode("utf-8", errors="replace")
        stderr = stderr_data.decode("utf-8", errors="replace")
        exit_code = process.returncode

        output = stdout.rstrip()
        if stderr.strip():
            output += "\n--- stderr ---\n" + stderr.rstrip()
        if exit_code != 0:
            output += f"\nExit code: {exit_code}"

        # Truncate very large output
        if len(output) > 100 * 1024:
            output = output[: 100 * 1024] + "\n... [output truncated]"

        return ToolResult(
            success=exit_code == 0,
            output=output,
            error=stderr if exit_code != 0 else None,
            exit_code=exit_code,
        )

    def _build_environment(self) -> dict[str, str]:
        env = os.environ.copy()
        policy = self.config.shell_environment
        if not policy.ignore_default_excludes:
            import fnmatch
            for pattern in policy.exclude_patterns:
                keys = [k for k in env if fnmatch.fnmatch(k.upper(), pattern.upper())]
                for k in keys:
                    del env[k]
        if policy.set_vars:
            env.update(policy.set_vars)
        return env
