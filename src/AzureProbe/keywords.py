"""Public Robot Framework keywords."""

import os
import time
from uuid import UUID

from robot.api.deco import keyword, library

from .powershell_runner import PowerShellRunner, positive_seconds


def _identifier(value: str, label: str) -> str:
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError(f"{label} must be an Azure UUID.") from exc


def _name(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string.")
    if any(char in value for char in "*?[]/\\\r\n\x00"):
        raise ValueError(f"{label} must be an exact name without wildcards or path separators.")
    return value


@library(scope="SUITE", version="0.1.0", auto_keywords=False)
class AzureProbe:
    """Read-only Azure VM checks implemented through Azure PowerShell.

    Import with an explicit ``subscription_id`` or set ``AZURE_SUBSCRIPTION_ID``.
    Sign in with Azure PowerShell before running tests. Each keyword uses a new
    PowerShell process, which loads a saved Az context or ``context_path``.
    ``command_timeout`` is a number of seconds for an individual query.
    """

    def __init__(
        self,
        subscription_id: str | None = None,
        tenant_id: str | None = None,
        context_path: str | None = None,
        powershell: str = "pwsh",
        command_timeout: float = 60,
    ):
        subscription = subscription_id or os.getenv("AZURE_SUBSCRIPTION_ID")
        if not subscription:
            raise ValueError("Provide subscription_id or set AZURE_SUBSCRIPTION_ID.")
        self._subscription_id = _identifier(subscription, "subscription_id")
        tenant = tenant_id or os.getenv("AZURE_TENANT_ID")
        self._tenant_id = _identifier(tenant, "tenant_id") if tenant else None
        self._context_path = context_path or os.getenv("AZUREPROBE_CONTEXT_PATH")
        if self._context_path:
            self._context_path = os.path.abspath(os.path.expanduser(self._context_path))
        self._runner = PowerShellRunner(powershell, command_timeout)

    def _query(self, resource_group: str, vm_name: str, timeout: float | None = None) -> dict:
        return self._runner.get_vm(
            {
                "subscription_id": self._subscription_id,
                "tenant_id": self._tenant_id,
                "context_path": self._context_path,
                "resource_group": _name(resource_group, "resource_group"),
                "vm_name": _name(vm_name, "vm_name"),
            },
            timeout=timeout,
        )

    @keyword("Get Azure VM")
    def get_azure_vm(self, resource_group: str, vm_name: str) -> dict:
        """Return normalized VM information; fail if the VM is missing.

        Keys: resource_id, name, resource_group, subscription_id, location,
        vm_size, provisioning_state, power_state, tags. Power state can be
        ``None`` if Azure has not supplied instance status yet.
        """
        result = self._query(resource_group, vm_name)
        if not result["found"]:
            raise AssertionError(f"Azure VM {vm_name!r} was not found in {resource_group!r}.")
        return result["vm"]

    @keyword("Azure VM Should Exist")
    def azure_vm_should_exist(self, resource_group: str, vm_name: str) -> dict:
        """Assert the VM exists and return its information."""
        return self.get_azure_vm(resource_group, vm_name)

    @keyword("Azure VM Property Should Be")
    def azure_vm_property_should_be(
        self, resource_group: str, vm_name: str, property_name: str, expected: str
    ):
        """Compare a normalized scalar property exactly (case-sensitive).

        For example: ``vm_size`` with ``Standard_B2s`` or ``location`` with
        ``westeurope``. Use ``Azure VM Should Have Tag`` for tags.
        """
        properties = {
            "resource_id",
            "name",
            "resource_group",
            "subscription_id",
            "location",
            "vm_size",
            "provisioning_state",
            "power_state",
        }
        if property_name not in properties:
            raise ValueError(f"Unknown VM property {property_name!r}; use {sorted(properties)}.")
        actual = self.get_azure_vm(resource_group, vm_name)[property_name]
        if actual != expected:
            raise AssertionError(
                f"Azure VM {vm_name!r}: {property_name} was {actual!r}; expected {expected!r}."
            )

    @keyword("Azure VM Should Have Tag")
    def azure_vm_should_have_tag(
        self, resource_group: str, vm_name: str, tag_name: str, expected: str | None = None
    ):
        """Check a tag exists, and optionally check its value.

        Tag names are matched case-insensitively, as in Azure. Values are exact.
        Omitting ``expected`` checks presence; an empty string checks an empty value.
        """
        if not tag_name:
            raise ValueError("tag_name must not be empty.")
        tags = self.get_azure_vm(resource_group, vm_name)["tags"]
        matches = [value for name, value in tags.items() if name.casefold() == tag_name.casefold()]
        if not matches:
            raise AssertionError(f"Azure VM {vm_name!r} has no tag {tag_name!r}.")
        if expected is not None and matches[0] != expected:
            raise AssertionError(
                f"Azure VM {vm_name!r}: tag {tag_name!r} was {matches[0]!r}; expected {expected!r}."
            )

    @keyword("Azure VM Power State Should Be")
    def azure_vm_power_state_should_be(
        self, resource_group: str, vm_name: str, expected: str = "running"
    ):
        """Check a power state, e.g. running, stopped, or deallocated."""
        expected = self._power_state(expected)
        actual = self.get_azure_vm(resource_group, vm_name)["power_state"]
        if actual != expected:
            raise AssertionError(
                f"Azure VM {vm_name!r}: power state was {actual!r}; expected {expected!r}."
            )

    @keyword("Wait Until Azure VM Power State Is")
    def wait_until_azure_vm_power_state_is(
        self,
        resource_group: str,
        vm_name: str,
        expected: str = "running",
        timeout: float = 120,
        poll_interval: float = 5,
    ) -> dict:
        """Poll until a power state matches and return the VM information.

        ``timeout`` and ``poll_interval`` are seconds. The timeout includes
        subprocess execution. Missing VMs and other states are retried;
        authentication, permissions, and query errors fail immediately.
        """
        timeout = positive_seconds(timeout, "timeout")
        poll_interval = positive_seconds(poll_interval, "poll_interval")
        expected = self._power_state(expected)
        deadline = time.monotonic() + timeout
        last = "not queried"
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            result = self._query(resource_group, vm_name, timeout=remaining)
            last = result["vm"]["power_state"] if result["found"] else "VM missing"
            if result["found"] and last == expected and time.monotonic() <= deadline:
                return result["vm"]
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(poll_interval, remaining))
        raise AssertionError(
            f"Azure VM {vm_name!r} did not reach {expected!r} within {timeout:g} seconds; "
            f"last state: {last!r}."
        )

    @staticmethod
    def _power_state(value: str) -> str:
        state = value.lower().removeprefix("powerstate/")
        valid = {
            "starting",
            "running",
            "stopping",
            "stopped",
            "deallocating",
            "deallocated",
            "hibernated",
            "unknown",
        }
        if state not in valid:
            raise ValueError(f"Unsupported power state {value!r}; use {sorted(valid)}.")
        return state
