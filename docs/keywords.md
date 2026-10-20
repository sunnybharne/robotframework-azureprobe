# Keyword reference

Import `AzureProbe` in the Robot Framework settings table.

## Library arguments

| Argument | Default | Meaning |
| --- | --- | --- |
| `subscription_id` | `AZURE_SUBSCRIPTION_ID` environment variable | Required Azure subscription UUID. |
| `tenant_id` | `AZURE_TENANT_ID` if present | Optional tenant UUID to select and verify. |
| `context_path` | `AZUREPROBE_CONTEXT_PATH` if present | Optional file created with `Save-AzContext`. |
| `powershell` | `pwsh` | Executable name or path. |
| `command_timeout` | `60` | Maximum seconds for an individual PowerShell query. |

No Azure query is performed when importing the library. Library scope is `SUITE`.

## Get Azure VM / Azure VM Should Exist

Arguments: `resource_group`, `vm_name`.

Returns a dictionary with these keys:

| Key | Example |
| --- | --- |
| `resource_id` | Full Azure Resource Manager VM resource ID |
| `name` | `vm-example` |
| `resource_group` | `rg-example` |
| `subscription_id` | Explicitly selected subscription UUID |
| `location` | `westeurope` |
| `vm_size` | `Standard_B2s` |
| `provisioning_state` | `Succeeded` |
| `power_state` | `running`, or Python `None` when no power status is returned |
| `tags` | A dictionary of tag names and string values |

Missing VMs fail the keyword. Authentication errors and authorization failures
are reported as execution errors, not interpreted as evidence that a VM is absent.

## Azure VM Property Should Be

Arguments: `resource_group`, `vm_name`, `property_name`, `expected`.

`property_name` must be a scalar key from the table above (everything except
`tags`). Comparison is exact and case-sensitive. Property paths into arbitrary
Azure SDK objects are not supported. This keeps the supported output schema clear.

## Azure VM Should Have Tag

Arguments: `resource_group`, `vm_name`, `tag_name`, `expected=None`.

Omit `expected` to check presence only. Supply `${EMPTY}` to check an empty value.
Tag names are case-insensitive; tag values are case-sensitive.

## Azure VM Power State Should Be

Arguments: `resource_group`, `vm_name`, `expected=running`.

Supported state names are `starting`, `running`, `stopping`, `stopped`,
`deallocating`, `deallocated`, `hibernated`, and `unknown`. Input is
case-insensitive, and a `PowerState/` prefix is accepted. Missing instance status
does not satisfy an `unknown` expectation; `unknown` requires an explicit Azure
status of that name.

## Wait Until Azure VM Power State Is

Arguments: `resource_group`, `vm_name`, `expected=running`, `timeout=120`,
`poll_interval=5`.

Durations are positive finite numbers in **seconds**, not Robot time strings.
The timeout includes PowerShell execution time. Each command gets the smaller
of `command_timeout` and the remaining overall budget. A process timeout raises
an execution error immediately. Normal state polling reports the last observed
state when its deadline expires. Successful polling returns the VM dictionary.

Queries use fresh processes, so very short intervals may spend most of their
time starting PowerShell and importing the Az modules.
