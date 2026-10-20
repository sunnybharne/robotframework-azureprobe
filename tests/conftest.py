import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def fake_azure(monkeypatch):
    """Run real PowerShell against test-only Azure module stand-ins, never Azure."""
    if not shutil.which("pwsh"):
        pytest.skip("PowerShell 7 is needed for the offline PowerShell integration checks")
    modules = Path(__file__).parent / "fixtures" / "modules"
    # PowerShell prepends user module directories on startup. Explicitly preload
    # the fixtures so production's Import-Module reuses them, regardless of local
    # Az installations. Keep this bootstrap entirely outside the shipped code.
    real_run = subprocess.run

    def run_with_fixtures(command, **kwargs):
        if "-File" not in command:
            return real_run(command, **kwargs)
        index = command.index("-File")
        script = command[index + 1]
        bootstrap = (
            "$ErrorActionPreference = 'Stop'; "
            "$env:PSModulePath = $env:AZUREPROBE_TEST_MODULE_ROOT + "
            "[System.IO.Path]::PathSeparator + (Join-Path $PSHOME 'Modules'); "
            "Import-Module (Join-Path $env:AZUREPROBE_TEST_MODULE_ROOT "
            "'Az.Accounts/Az.Accounts.psm1') -Force; "
            "Import-Module (Join-Path $env:AZUREPROBE_TEST_MODULE_ROOT "
            "'Az.Compute/Az.Compute.psm1') -Force; "
            "& $env:AZUREPROBE_TEST_SCRIPT_PATH"
        )
        environment = dict(os.environ)
        environment["AZUREPROBE_TEST_MODULE_ROOT"] = str(modules)
        environment["AZUREPROBE_TEST_SCRIPT_PATH"] = script
        kwargs["env"] = environment
        return real_run([*command[:index], "-Command", bootstrap], **kwargs)

    monkeypatch.setattr("AzureProbe.powershell_runner.subprocess.run", run_with_fixtures)
    monkeypatch.delenv("AZURE_TENANT_ID", raising=False)
    monkeypatch.delenv("AZUREPROBE_CONTEXT_PATH", raising=False)
    monkeypatch.setenv("AZUREPROBE_TEST_SCENARIO", "running")
    return monkeypatch
