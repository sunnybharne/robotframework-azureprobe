"""Transport JSON to a bundled script without interpolating executable commands."""

import json
import math
import subprocess
from importlib.resources import as_file, files


class PowerShellError(RuntimeError):
    """PowerShell, authentication, or the Azure query failed."""


def positive_seconds(value: float, name: str) -> float:
    """Require a finite duration so polling and processes are always bounded."""
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{name} must be a positive, finite number of seconds.")
    return number


class PowerShellRunner:
    def __init__(self, executable: str = "pwsh", timeout: float = 60):
        self.executable = executable
        self.timeout = positive_seconds(timeout, "command_timeout")

    def get_vm(self, payload: dict, timeout: float | None = None) -> dict:
        budget = (
            self.timeout
            if timeout is None
            else min(self.timeout, positive_seconds(timeout, "timeout"))
        )
        script = files("AzureProbe").joinpath("scripts", "Get-AzureVm.ps1")
        try:
            with as_file(script) as script_path:
                completed = subprocess.run(
                    [
                        self.executable,
                        "-NoLogo",
                        "-NoProfile",
                        "-NonInteractive",
                        "-File",
                        str(script_path),
                    ],
                    input=json.dumps(payload, ensure_ascii=True),
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=budget,
                    check=False,
                )
        except FileNotFoundError as exc:
            raise PowerShellError(
                f"PowerShell executable {self.executable!r} was not found. "
                "Install PowerShell 7 and add pwsh to PATH."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise PowerShellError(f"Azure VM query exceeded {budget:g} seconds.") from exc
        except OSError as exc:
            raise PowerShellError("Could not start the PowerShell executable.") from exc

        if completed.returncode:
            # The script emits a concise error on stderr; never include stdin or stdout.
            detail = completed.stderr.strip() or "No error details were returned."
            raise PowerShellError(
                f"Azure PowerShell query failed (exit {completed.returncode}): {detail}"
            )
        try:
            result = json.loads(completed.stdout.lstrip("\ufeff"))
        except (ValueError, TypeError) as exc:
            raise PowerShellError("PowerShell did not return a valid JSON result.") from exc
        if not isinstance(result, dict) or type(result.get("found")) is not bool:
            raise PowerShellError("PowerShell returned an invalid VM result envelope.")
        if result["found"]:
            vm = result.get("vm")
            required = {
                "resource_id",
                "name",
                "resource_group",
                "subscription_id",
                "location",
                "vm_size",
                "provisioning_state",
                "power_state",
                "tags",
            }
            if not isinstance(vm, dict) or not required.issubset(vm):
                raise PowerShellError("PowerShell returned incomplete VM information.")
            if not isinstance(vm["tags"], dict):
                raise PowerShellError("PowerShell returned invalid VM tags.")
            if any(
                value is not None and not isinstance(value, str)
                for key, value in vm.items()
                if key in required - {"tags"}
            ):
                raise PowerShellError("PowerShell returned invalid VM property types.")
        return result
