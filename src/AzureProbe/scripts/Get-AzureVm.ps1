# Read-only Azure VM query. Request and response are JSON; no input is evaluated as code.
#Requires -Version 7.0
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$WarningPreference = 'SilentlyContinue'
$InformationPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

function Test-ResourceNotFound {
    param([System.Management.Automation.ErrorRecord] $Failure)
    $exception = $Failure.Exception
    while ($null -ne $exception) {
        if ($exception.PSObject.Properties['Response'] -and $null -ne $exception.Response) {
            if ($exception.Response.PSObject.Properties['StatusCode'] -and
                [int]$exception.Response.StatusCode -eq 404) { return $true }
        }
        if ($exception.PSObject.Properties['StatusCode'] -and
            $null -ne $exception.StatusCode -and [int]$exception.StatusCode -eq 404) {
            return $true
        }
        $exception = $exception.InnerException
    }
    if ($Failure.ErrorDetails -and $Failure.ErrorDetails.Message) {
        try {
            $details = $Failure.ErrorDetails.Message | ConvertFrom-Json -ErrorAction Stop
            return $details.error.code -in @('ResourceNotFound', 'ResourceGroupNotFound')
        } catch { return $false }
    }
    return $false
}

try {
    $request = [Console]::In.ReadToEnd() | ConvertFrom-Json -AsHashtable
    if (-not $request.subscription_id -or -not $request.resource_group -or -not $request.vm_name) {
        throw 'subscription_id, resource_group and vm_name are required.'
    }
    Import-Module Az.Accounts -ErrorAction Stop
    Import-Module Az.Compute -ErrorAction Stop
    Disable-AzContextAutosave -Scope Process | Out-Null
    if ($request.context_path) {
        Import-AzContext -Path $request.context_path -Scope Process -ErrorAction Stop | Out-Null
    }

    $contextArgs = @{ Subscription = $request.subscription_id; Scope = 'Process'; ErrorAction = 'Stop' }
    if ($request.tenant_id) { $contextArgs.Tenant = $request.tenant_id }
    $context = Set-AzContext @contextArgs
    if ($null -eq $context -or $context.Subscription.Id -ne $request.subscription_id) {
        throw 'No matching Azure subscription context. Sign in with Connect-AzAccount first.'
    }
    if ($request.tenant_id -and $context.Tenant.Id -ne $request.tenant_id) {
        throw 'The selected Azure context does not match the requested tenant.'
    }

    $query = @{
        ResourceGroupName = $request.resource_group
        Name = $request.vm_name
        DefaultProfile = $context
        ErrorAction = 'Stop'
    }
    try {
        $model = Get-AzVM @query
        if ($null -eq $model) {
            @{ found = $false } | ConvertTo-Json -Compress
            exit 0
        }
        $instance = Get-AzVM @query -Status
    } catch {
        if (Test-ResourceNotFound $_) {
            @{ found = $false } | ConvertTo-Json -Compress
            exit 0
        }
        throw
    }

    $state = @($instance.Statuses | Where-Object { $_.Code -like 'PowerState/*' } |
        Select-Object -First 1)
    $powerState = $null
    if ($state.Count -gt 0) { $powerState = ($state[0].Code -split '/', 2)[1].ToLowerInvariant() }
    $tags = @{}
    if ($model.Tags) {
        foreach ($key in $model.Tags.Keys) { $tags[$key] = [string]$model.Tags[$key] }
    }
    @{
        found = $true
        vm = @{
            resource_id = $model.Id
            name = $model.Name
            resource_group = $request.resource_group
            subscription_id = $context.Subscription.Id
            location = $model.Location
            vm_size = $model.HardwareProfile.VmSize
            provisioning_state = $model.ProvisioningState
            power_state = $powerState
            tags = $tags
        }
    } | ConvertTo-Json -Depth 8 -Compress
} catch {
    [Console]::Error.WriteLine(('Azure query failed: {0}' -f $_.Exception.Message))
    exit 1
}
