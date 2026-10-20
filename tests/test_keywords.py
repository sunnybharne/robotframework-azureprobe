from unittest.mock import Mock

import pytest

from AzureProbe import AzureProbe
from AzureProbe.powershell_runner import PowerShellError

SUBSCRIPTION = "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def probe(monkeypatch):
    monkeypatch.delenv("AZURE_TENANT_ID", raising=False)
    monkeypatch.delenv("AZUREPROBE_CONTEXT_PATH", raising=False)
    instance = AzureProbe(SUBSCRIPTION)
    instance._runner = Mock()
    instance._runner.get_vm.return_value = {
        "found": True,
        "vm": {
            "name": "demo",
            "location": "westeurope",
            "vm_size": "Standard_B2s",
            "power_state": "running",
            "tags": {"Environment": "test", "Empty": ""},
        },
    }
    return instance


def test_explicit_subscription_required(monkeypatch):
    monkeypatch.delenv("AZURE_SUBSCRIPTION_ID", raising=False)
    with pytest.raises(ValueError, match="subscription_id"):
        AzureProbe()


def test_environment_subscription_supported(monkeypatch):
    monkeypatch.setenv("AZURE_SUBSCRIPTION_ID", SUBSCRIPTION)
    monkeypatch.delenv("AZURE_TENANT_ID", raising=False)
    assert AzureProbe()._subscription_id == SUBSCRIPTION


def test_malformed_subscription_rejected():
    with pytest.raises(ValueError, match="UUID"):
        AzureProbe("some-subscription")


@pytest.mark.parametrize("name", ["*", "vm?", "vm[123]", "vm/other", "", "\n"])
def test_exact_resource_names_required(probe, name):
    with pytest.raises(ValueError):
        probe.get_azure_vm("rg-test", name)
    probe._runner.get_vm.assert_not_called()


def test_matching_vm_properties_and_tags(probe):
    probe.azure_vm_property_should_be("rg", "demo", "vm_size", "Standard_B2s")
    probe.azure_vm_should_have_tag("rg", "demo", "environment", "test")
    probe.azure_vm_should_have_tag("rg", "demo", "Environment")
    probe.azure_vm_should_have_tag("rg", "demo", "Empty", "")
    probe.azure_vm_power_state_should_be("rg", "demo", "PowerState/RUNNING")


@pytest.mark.parametrize(
    "check,args",
    [
        ("azure_vm_property_should_be", ("location", "eastus")),
        ("azure_vm_should_have_tag", ("missing",)),
        ("azure_vm_should_have_tag", ("Environment", "production")),
        ("azure_vm_should_have_tag", ("Environment", "")),
        ("azure_vm_power_state_should_be", ("stopped",)),
    ],
)
def test_mismatches_fail(probe, check, args):
    with pytest.raises(AssertionError):
        getattr(probe, check)("rg", "demo", *args)


def test_unknown_property_fails_before_query(probe):
    with pytest.raises(ValueError, match="Unknown VM property"):
        probe.azure_vm_property_should_be("rg", "demo", "imaginary", "value")
    probe._runner.get_vm.assert_not_called()


def test_unknown_power_state_fails_before_query(probe):
    with pytest.raises(ValueError, match="Unsupported power state"):
        probe.azure_vm_power_state_should_be("rg", "demo", "ruuning")
    probe._runner.get_vm.assert_not_called()


def test_polling_waits_through_missing_and_stopped_states(probe, monkeypatch):
    clock = [0.0]
    monkeypatch.setattr("AzureProbe.keywords.time.monotonic", lambda: clock[0])
    monkeypatch.setattr(
        "AzureProbe.keywords.time.sleep", lambda delay: clock.__setitem__(0, clock[0] + delay)
    )
    probe._runner.get_vm.side_effect = [
        {"found": False},
        {"found": True, "vm": {"power_state": "stopped"}},
        {"found": True, "vm": {"power_state": "running"}},
    ]
    assert (
        probe.wait_until_azure_vm_power_state_is("rg", "demo", timeout=10, poll_interval=2)[
            "power_state"
        ]
        == "running"
    )
    assert [call.kwargs["timeout"] for call in probe._runner.get_vm.call_args_list] == [10, 8, 6]


def test_polling_timeout_is_bounded_and_reports_last_state(probe, monkeypatch):
    clock = [0.0]
    monkeypatch.setattr("AzureProbe.keywords.time.monotonic", lambda: clock[0])
    monkeypatch.setattr(
        "AzureProbe.keywords.time.sleep", lambda delay: clock.__setitem__(0, clock[0] + delay)
    )
    probe._runner.get_vm.return_value = {"found": True, "vm": {"power_state": "stopped"}}
    with pytest.raises(AssertionError, match="last state: 'stopped'"):
        probe.wait_until_azure_vm_power_state_is("rg", "demo", timeout=3, poll_interval=2)
    assert clock[0] == 3


def test_polling_does_not_swallow_authentication_failures(probe):
    probe._runner.get_vm.side_effect = PowerShellError("Permission denied")
    with pytest.raises(PowerShellError, match="Permission denied"):
        probe.wait_until_azure_vm_power_state_is("rg", "demo")
    assert probe._runner.get_vm.call_count == 1


@pytest.mark.parametrize("value", [0, -1, float("inf"), float("nan")])
def test_invalid_poll_durations_rejected(probe, value):
    with pytest.raises(ValueError):
        probe.wait_until_azure_vm_power_state_is("rg", "demo", timeout=value)
