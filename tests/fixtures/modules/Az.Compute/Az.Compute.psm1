# Test-only module. Values imitate the model and instance views from Get-AzVM.
function Get-AzVM {
    [CmdletBinding()]
    param([string] $ResourceGroupName, [string] $Name, $DefaultProfile, [switch] $Status)
    if (-not $DefaultProfile.Subscription.Id) { throw 'An explicit Azure context is required.' }
    switch ($env:AZUREPROBE_TEST_SCENARIO) {
        'missing' {
            throw [System.Net.Http.HttpRequestException]::new(
                'Resource does not exist.', $null, [System.Net.HttpStatusCode]::NotFound)
        }
        'null' { return $null }
        'forbidden' {
            throw [System.Net.Http.HttpRequestException]::new(
                'Access denied.', $null, [System.Net.HttpStatusCode]::Forbidden)
        }
        'throttled' {
            throw [System.Net.Http.HttpRequestException]::new(
                'Rate limited.', $null, [System.Net.HttpStatusCode]::TooManyRequests)
        }
    }
    if ($Status) {
        if ($env:AZUREPROBE_TEST_SCENARIO -eq 'deleted-between-queries') {
            throw [System.Net.Http.HttpRequestException]::new(
                'Resource was deleted.', $null, [System.Net.HttpStatusCode]::NotFound)
        }
        if ($env:AZUREPROBE_TEST_SCENARIO -eq 'no-state') {
            return [PSCustomObject]@{ Statuses = @() }
        }
        $state = 'running'
        if ($env:AZUREPROBE_TEST_SCENARIO -eq 'stopped') { $state = 'stopped' }
        return [PSCustomObject]@{
            Statuses = @([PSCustomObject]@{ Code = "PowerState/$state" })
        }
    }
    [PSCustomObject]@{
        Id = "/subscriptions/$($DefaultProfile.Subscription.Id)/resourceGroups/$ResourceGroupName/providers/Microsoft.Compute/virtualMachines/$Name"
        Name = $Name
        Location = 'westeurope'
        HardwareProfile = [PSCustomObject]@{ VmSize = 'Standard_B2s' }
        ProvisioningState = 'Succeeded'
        Tags = @{ Environment = 'test'; Empty = ''; Unicode = 'Helsinki — 测试' }
    }
}

Export-ModuleMember -Function Get-AzVM
