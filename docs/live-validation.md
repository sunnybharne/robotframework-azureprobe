# Validate AzureProbe against a real Azure VM

These steps use an **existing, running test VM**. They read its configuration
and state; they do not create resources or change the VM. Run the commands in
PowerShell 7 from the repository root, with the Python environment activated.

The automated offline suite uses fake Azure modules. This guide is the separate
live check that verifies authentication, actual Az module behavior, and access
to your chosen subscription. Completing the guide is still pending.

## 1. Install and sign in

```powershell
python -m pip install .
Install-Module -Name Az.Accounts, Az.Compute -Scope CurrentUser -Repository PSGallery
Connect-AzAccount

$env:AZURE_SUBSCRIPTION_ID = '<subscription UUID>'
$resourceGroup = '<existing resource group>'
$vmName = '<existing running VM name>'
$context = Set-AzContext -Subscription $env:AZURE_SUBSCRIPTION_ID -Scope Process
```

Use an account with permission to read the target VM and its instance view.
If selecting a tenant is necessary, pass `-Tenant '<tenant UUID>'` to sign-in and
context selection, then set `AZURE_TENANT_ID` to that tenant UUID for AzureProbe.
For another Azure cloud environment, sign in to that environment explicitly.

Confirm the subscription selected above is the one you intend to inspect:

```powershell
$context.Subscription | Select-Object Name, Id
Get-AzVM -ResourceGroupName $resourceGroup -Name $vmName -DefaultProfile $context |
    Select-Object Name, Location, ProvisioningState,
        @{ Name = 'VmSize'; Expression = { $_.HardwareProfile.VmSize } }, Tags
Get-AzVM -ResourceGroupName $resourceGroup -Name $vmName -Status -DefaultProfile $context |
    Select-Object -ExpandProperty Statuses
```

If these direct Azure commands fail, resolve sign-in, subscription selection,
resource naming, or read permissions before testing the library.

## 2. Make the context available to child processes

AzureProbe starts a new PowerShell process for each query. Export the authenticated
context explicitly so this also works when the parent login is process-scoped:

```powershell
$contextFile = Join-Path ([System.IO.Path]::GetTempPath()) (
    'azureprobe-' + [guid]::NewGuid().ToString('N') + '.context.json'
)
Save-AzContext -Path $contextFile -Force
$env:AZUREPROBE_CONTEXT_PATH = $contextFile
```

Treat this file as sensitive authentication context. Keep it outside the repository,
restrict access to your account, and remove it after the run. The current library
imports existing Az contexts; it does not establish a login from Azure CLI or
automatically configure managed identity or federated authentication.

## 3. Run the positive checks

Choose expected values from your deployment requirements. The values below are
examples: replace them with your intended VM location, size, and environment tag.
Using the VM's current settings as expectations only proves the test can read them;
using your intended configuration checks that the deployment is correct.

```powershell
python -m robot --outputdir results/live-positive `
    --variable "RESOURCE_GROUP:$resourceGroup" `
    --variable "VM_NAME:$vmName" `
    --variable "EXPECTED_LOCATION:westeurope" `
    --variable "EXPECTED_SIZE:Standard_B2s" `
    --variable "EXPECTED_ENVIRONMENT:test" `
    examples/vm_checks.robot
```

**Expected result:** five passing Robot tests and exit code `0`. The suite checks
existence and configuration, the environment tag, running state, waiting for
running state, and successful provisioning. Since the target VM is already
running, this live smoke check does not exercise a real state transition.

Inspect `results/live-positive/log.html` if an assertion fails.

## 4. Confirm an incorrect expectation fails

This deliberately uses an impossible location expectation against the same VM:

```powershell
python -m robot --outputdir results/live-wrong-location `
    --test 'VM Exists And Has Expected Configuration' `
    --variable "RESOURCE_GROUP:$resourceGroup" `
    --variable "VM_NAME:$vmName" `
    --variable EXPECTED_LOCATION:azureprobe-intentional-mismatch `
    examples/vm_checks.robot
```

**Expected result:** one failed test and exit code `1`, with a message comparing
the actual location to the incorrect expectation. This is a successful negative
check only when it fails for the expected property mismatch, not an auth or
transport error. It makes no change to the VM.

## 5. Confirm a nonexistent VM fails clearly

Generate a unique name for a resource that has not been created:

```powershell
$missingName = 'azureprobe-missing-' + [guid]::NewGuid().ToString('N').Substring(0, 8)
python -m robot --outputdir results/live-missing-vm `
    --test 'VM Exists And Has Expected Configuration' `
    --variable "RESOURCE_GROUP:$resourceGroup" `
    --variable "VM_NAME:$missingName" `
    examples/vm_checks.robot
```

**Expected result:** one failed test and exit code `1`, specifically stating that
the VM was not found. A permission failure must remain an execution error; it
does not establish that a resource is absent.

## 6. Record results and remove the exported context

Record the Git commit, operating system, runtime and module versions, the positive
suite outcome, and the two expected negative outcomes:

```powershell
git rev-parse HEAD
python --version
python -m robot --version
$PSVersionTable.PSVersion.ToString()
Get-Module Az.Accounts, Az.Compute | Select-Object Name, Version

Remove-Item -LiteralPath $contextFile
Remove-Item Env:AZUREPROBE_CONTEXT_PATH
```

Review Robot reports before sharing: they can contain subscription IDs, resource
names, and tags. Record a sanitized result summary in the project rather than
committing raw reports or exported authentication context.

| Symptom | Next step |
| --- | --- |
| `pwsh` not found | Install PowerShell 7 and ensure it is on PATH. |
| Az module import fails | Install Az.Accounts and Az.Compute for the same PowerShell installation. |
| Sign-in works in the parent but fails in AzureProbe | Export the context and provide `AZUREPROBE_CONTEXT_PATH`. |
| Subscription or tenant mismatch | Check the supplied UUIDs and selected sign-in context. |
| Access denied | Check read permissions for the VM and its instance view. |
| Query exceeds its timeout | Increase the library's `command_timeout` if module startup or Azure responses are slow. |
| VM exists but is not running | Choose a running test VM or write a test with the intended power state. |

References: [Azure PowerShell contexts](https://learn.microsoft.com/en-us/powershell/azure/context-persistence),
[Get-AzVM](https://learn.microsoft.com/en-us/powershell/module/az.compute/get-azvm).
