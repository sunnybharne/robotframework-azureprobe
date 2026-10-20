import json
import subprocess
from unittest.mock import patch

import pytest

from AzureProbe.powershell_runner import PowerShellError, PowerShellRunner


def test_request_is_sent_on_stdin_and_timeout_is_capped():
    payload = {"vm_name": "'; throw 'unsafe"}
    result = subprocess.CompletedProcess([], 0, '{"found":false}', "")
    with patch("AzureProbe.powershell_runner.subprocess.run", return_value=result) as run:
        assert PowerShellRunner(timeout=10).get_vm(payload, timeout=3) == {"found": False}
    args, kwargs = run.call_args
    assert "-File" in args[0]
    assert payload["vm_name"] not in args[0]
    assert json.loads(kwargs["input"]) == payload
    assert kwargs["timeout"] == 3
    assert kwargs.get("shell", False) is False


@pytest.mark.parametrize(
    "output",
    ["", "not json", "[]", '{"found":"false"}', '{"found":true}', '{"found":true,"vm":{}}'],
)
def test_malformed_output_cannot_be_a_success(output):
    result = subprocess.CompletedProcess([], 0, output, "")
    with patch("AzureProbe.powershell_runner.subprocess.run", return_value=result):
        with pytest.raises(PowerShellError):
            PowerShellRunner().get_vm({})


def test_nonzero_exit_is_never_a_success():
    result = subprocess.CompletedProcess([], 1, '{"found":true}', "Access denied")
    with patch("AzureProbe.powershell_runner.subprocess.run", return_value=result):
        with pytest.raises(PowerShellError, match="Access denied"):
            PowerShellRunner().get_vm({})


@pytest.mark.parametrize(
    "error,match",
    [
        (FileNotFoundError(), "Install PowerShell 7"),
        (subprocess.TimeoutExpired("pwsh", 1), "exceeded"),
    ],
)
def test_transport_errors_are_actionable(error, match):
    with patch("AzureProbe.powershell_runner.subprocess.run", side_effect=error):
        with pytest.raises(PowerShellError, match=match):
            PowerShellRunner().get_vm({})
