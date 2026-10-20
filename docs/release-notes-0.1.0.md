# AzureProbe 0.1.0 — initial alpha

**Draft release notes. The package has not been published to PyPI.**

AzureProbe brings reusable Azure VM checks to Robot Framework through Azure
PowerShell. Test authors can check infrastructure using readable keywords while
the library handles PowerShell execution and the Azure query results.

## Included

- `Get Azure VM`
- `Azure VM Should Exist`
- `Azure VM Property Should Be`
- `Azure VM Should Have Tag`
- `Azure VM Power State Should Be`
- `Wait Until Azure VM Power State Is`

The release includes installation and authentication guidance, an example Robot
suite, a keyword reference, packaging configuration, offline automated checks,
and GitHub Actions configuration.

## Requirements

Python 3.10+, Robot Framework 7, PowerShell 7, Az.Accounts, Az.Compute, and an
authenticated Azure PowerShell context with permission to read the target VM.

## Validation and limitations

Local validation passed 47 automated checks, including a five-case Robot suite
using the actual PowerShell script with isolated fake Azure modules. The wheel
also installed in a fresh environment, included its PowerShell script, and passed
a Robot dry run. These checks used Python 3.10.11, Robot Framework 7.5, and
PowerShell 7.5.3 on macOS.

Live Azure VM checks are still pending. Support is currently limited to VM inspection; application
health, other Azure resource types, and resource provisioning are outside this
initial release.

Install from the repository using the README. Replace this installation note
with the published package command only after a PyPI release exists.
