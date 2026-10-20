# Test-only module. No cloud commands or authentication are performed.
function Disable-AzContextAutosave {
    [CmdletBinding()]
    param([string] $Scope)
    if ($Scope -ne 'Process') { throw 'Tests require process-only context changes.' }
}

function Import-AzContext {
    [CmdletBinding()]
    param([string] $Path, [string] $Scope)
    if ($Scope -ne 'Process') { throw 'Context import must use Process scope.' }
    if (-not (Test-Path -LiteralPath $Path)) { throw 'Context file missing.' }
}

function Set-AzContext {
    [CmdletBinding()]
    param([string] $Subscription, [string] $Tenant, [string] $Scope)
    if ($Scope -ne 'Process') { throw 'Context selection must use Process scope.' }
    if ($env:AZUREPROBE_TEST_SCENARIO -eq 'unauthenticated') { throw 'Please sign in first.' }
    if ($env:AZUREPROBE_TEST_SCENARIO -eq 'wrong-subscription') {
        $Subscription = '99999999-9999-9999-9999-999999999999'
    }
    if ($env:AZUREPROBE_TEST_SCENARIO -eq 'wrong-tenant') {
        $Tenant = '99999999-9999-9999-9999-999999999999'
    }
    [PSCustomObject]@{
        Subscription = [PSCustomObject]@{ Id = $Subscription }
        Tenant = [PSCustomObject]@{ Id = $Tenant }
    }
}

Export-ModuleMember -Function Disable-AzContextAutosave, Import-AzContext, Set-AzContext
