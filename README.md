# AzureProbe

Robot Framework keywords for checking **Azure virtual machines through PowerShell**.

AzureProbe exposes readable test keywords backed by `Get-AzVM` from Microsoft's
`Az.Compute` module. Version 0.1.0 is an initial alpha for existing Azure VMs.
It checks existence, configuration, tags, and power state. It performs no resource
creation, deletion, or configuration changes.

```robotframework
*** Settings ***
Library    AzureProbe    subscription_id=%{AZURE_SUBSCRIPTION_ID}

*** Test Cases ***
Application VM is ready
    Azure VM Should Exist             rg-example    vm-example
    Azure VM Power State Should Be    rg-example    vm-example    running
    Azure VM Property Should Be       rg-example    vm-example    location    westeurope
    Azure VM Should Have Tag          rg-example    vm-example    environment    test
```

## Prerequisites

- Python 3.10 or later and Robot Framework 7 (installed as a Python dependency).
- PowerShell 7, available as `pwsh` on your PATH.
- Azure PowerShell modules `Az.Accounts` and `Az.Compute`, installed separately.
- An authenticated Azure PowerShell context and permission to read the target VM
  and its instance view. Azure Reader at the appropriate resource scope is a usual
  starting point; custom roles must include the equivalent read operations.
- An explicit subscription ID, so checks always select the intended subscription.

PowerShell and Az modules are system prerequisites; installing the Python package
does not install them. The CI configuration exercises Windows, Linux, and macOS
with fake Azure modules. Real subscription behavior still needs live validation.

## Install from this repository

```shell
git clone https://github.com/sunnybharne/robotframework-azureprobe.git
cd robotframework-azureprobe
python -m venv .venv
```

Activate the environment using `source .venv/bin/activate` on macOS/Linux or
`.venv\Scripts\Activate.ps1` in Windows PowerShell. Then:

```shell
python -m pip install .
```

The project is not yet published to PyPI. The intended distribution name is
`robotframework-azureprobe`; the Robot library import name is `AzureProbe`.

## Install Azure modules and sign in

Run these commands in **PowerShell 7**:

```powershell
Install-Module -Name Az.Accounts, Az.Compute -Scope CurrentUser -Repository PSGallery
Connect-AzAccount
$env:AZURE_SUBSCRIPTION_ID = '<your-subscription-id>'

# Use a resource group and VM that already exist in your test subscription.
python -m robot --outputdir results `
    --variable RESOURCE_GROUP:rg-example `
    --variable VM_NAME:vm-example `
    examples/vm_checks.robot
```

The example also checks `location=westeurope`, `vm_size=Standard_B2s`, and the tag
`environment=test`. Override `EXPECTED_LOCATION`, `EXPECTED_SIZE`, and
`EXPECTED_ENVIRONMENT` with `--variable` to match your test environment.

Each query starts a new noninteractive PowerShell process. A login that exists
only inside the parent process will not automatically carry over. Normal Az
context persistence can supply the login to child processes. If autosave is
disabled or a pipeline uses a process-scoped login, explicitly export a context:

```powershell
Save-AzContext -Path "$env:TEMP/azureprobe.context.json" -Force
$env:AZUREPROBE_CONTEXT_PATH = "$env:TEMP/azureprobe.context.json"
```

On macOS/Linux, choose a path in your temporary directory instead of `$env:TEMP`
if that variable is unset. Protect exported context files, keep them outside Git,
and remove them when finished. AzureProbe only imports existing contexts; it does
not open an interactive login or manage login credentials. Azure CLI login alone
does not establish an Azure PowerShell context.

Context changes in child processes use `-Scope Process`. The library verifies
the selected subscription and, when provided, tenant before querying the VM.
See Microsoft's [Azure context documentation](https://learn.microsoft.com/en-us/powershell/azure/context-persistence).

## Keywords

| Keyword | Purpose |
| --- | --- |
| `Get Azure VM` | Return a dictionary of normalized VM properties. |
| `Azure VM Should Exist` | Assert existence and return the same dictionary. |
| `Azure VM Property Should Be` | Compare a supported scalar property with an expected value. |
| `Azure VM Should Have Tag` | Check a tag exists and optionally check its value. |
| `Azure VM Power State Should Be` | Check the current VM power state. |
| `Wait Until Azure VM Power State Is` | Poll for an expected power state within a timeout. |

Every keyword starts with `resource_group` and `vm_name`. Names must identify a
single resource; wildcard queries are rejected. [Full keyword reference](docs/keywords.md).

```robotframework
*** Settings ***
Library    AzureProbe
...    subscription_id=%{AZURE_SUBSCRIPTION_ID}
...    command_timeout=60

*** Test Cases ***
VM becomes ready after a separate deployment
    ${vm}=    Wait Until Azure VM Power State Is
    ...    rg-example    vm-example    running    timeout=120    poll_interval=5
    Should Be Equal    ${vm}[provisioning_state]    Succeeded
```

VM running state alone does not establish application health. Test the deployed
application's health endpoint separately.

## How it works

```text
Robot test -> Python keyword -> bundled PowerShell script -> Get-AzVM
                                                      <- Azure VM data
           <- assertion result / dictionary <- normalized JSON
```

The PowerShell script requests both model information and instance status. Python
passes parameters as JSON on stdin, without constructing shell commands from
resource names. The script emits a small normalized result. Missing resources
produce assertion failures; authentication, permissions, throttling, malformed
output, and process failures produce execution errors. Polling retries a missing
VM or an unexpected state, but fails immediately on execution errors.

## Development

```shell
python -m pip install -e '.[dev]'
python -m ruff check .
python -m pytest
python -m build
```

Tests use test-only Az module stand-ins. They exercise the actual PowerShell
script and a real Robot suite without contacting Azure. PowerShell checks are
skipped locally if `pwsh` is unavailable; CI requires PowerShell to be present.
Unit tests also cover failure messages, malformed output, argument handling, and
bounded polling. Test fixtures are excluded from the installed wheel.

Generate browsable keyword documentation:

```shell
python -m robot.libdoc AzureProbe::00000000-0000-0000-0000-000000000001 docs/keywords.html
```

Generating documentation does not query Azure. See [CONTRIBUTING.md](CONTRIBUTING.md)
for development checks and [the release guide](docs/releasing.md) for packaging.
To verify a real VM, follow the [live Azure validation guide](docs/live-validation.md).

## Status and roadmap

The first release targets Azure VMs only. Future additions may include resource
groups, storage accounts, and network configuration checks. Initial validation
uses offline stand-ins; successful automated checks are not evidence of a live
Azure deployment test. Record live validation separately before claiming support
for particular Az module versions or Azure environments.

AzureProbe is an independent community project. It uses
[Robot Framework's custom library interface](https://docs.robotframework.org/docs/extending_robot_framework/custom-libraries/python_library)
and Microsoft's [Get-AzVM cmdlet](https://learn.microsoft.com/en-us/powershell/module/az.compute/get-azvm).

Licensed under [MIT](LICENSE).
