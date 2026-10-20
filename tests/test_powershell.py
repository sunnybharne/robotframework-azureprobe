import pytest

from AzureProbe import AzureProbe
from AzureProbe.powershell_runner import PowerShellError

SUBSCRIPTION = "00000000-0000-0000-0000-000000000001"

pytestmark = pytest.mark.powershell


def test_script_returns_normalized_vm_with_real_powershell(fake_azure):
    vm = AzureProbe(SUBSCRIPTION).get_azure_vm("rg-test", "vm-test")
    assert vm["name"] == "vm-test"
    assert vm["subscription_id"] == SUBSCRIPTION
    assert vm["vm_size"] == "Standard_B2s"
    assert vm["power_state"] == "running"
    assert vm["tags"]["Unicode"] == "Helsinki — 测试"


@pytest.mark.parametrize("scenario", ["missing", "null", "deleted-between-queries"])
def test_missing_vm_is_an_assertion_failure(fake_azure, scenario):
    fake_azure.setenv("AZUREPROBE_TEST_SCENARIO", scenario)
    with pytest.raises(AssertionError, match="was not found"):
        AzureProbe(SUBSCRIPTION).azure_vm_should_exist("rg-test", "vm-missing")


@pytest.mark.parametrize(
    "scenario",
    [
        "forbidden",
        "throttled",
        "unauthenticated",
        "wrong-subscription",
        "wrong-tenant",
    ],
)
def test_execution_failures_are_never_reported_as_missing(fake_azure, scenario):
    fake_azure.setenv("AZUREPROBE_TEST_SCENARIO", scenario)
    with pytest.raises(PowerShellError):
        AzureProbe(SUBSCRIPTION, tenant_id=SUBSCRIPTION).get_azure_vm("rg-test", "vm-test")


def test_missing_instance_state_does_not_claim_vm_is_running(fake_azure):
    fake_azure.setenv("AZUREPROBE_TEST_SCENARIO", "no-state")
    assert AzureProbe(SUBSCRIPTION).get_azure_vm("rg-test", "vm-test")["power_state"] is None


def test_arguments_are_data_not_powershell_source(fake_azure):
    name = "literal'; throw 'injection"
    assert AzureProbe(SUBSCRIPTION).get_azure_vm("rg-test", name)["name"] == name


def test_explicit_context_import(fake_azure, tmp_path):
    context = tmp_path / "saved.context.json"
    context.write_text("{}")
    assert (
        AzureProbe(SUBSCRIPTION, context_path=str(context)).get_azure_vm("rg-test", "vm-test")[
            "power_state"
        ]
        == "running"
    )
