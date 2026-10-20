from pathlib import Path

import pytest
from robot import run
from robot.api import ExecutionResult


@pytest.mark.powershell
def test_real_robot_suite_through_powershell(fake_azure, tmp_path):
    suite = Path(__file__).parents[1] / "examples" / "vm_checks.robot"
    result = run(
        str(suite),
        outputdir=str(tmp_path),
        log="NONE",
        report="NONE",
        variable=[
            "SUBSCRIPTION_ID:00000000-0000-0000-0000-000000000001",
            "RESOURCE_GROUP:rg-test",
            "VM_NAME:vm-test",
        ],
    )
    assert result == 0
    stats = ExecutionResult(str(tmp_path / "output.xml")).statistics.total
    assert stats.passed == 5
    assert stats.failed == 0
