*** Settings ***
Documentation     Checks an existing Azure VM. Override the variables for your environment.
Library           AzureProbe    subscription_id=${SUBSCRIPTION_ID}

*** Variables ***
${SUBSCRIPTION_ID}         %{AZURE_SUBSCRIPTION_ID=00000000-0000-0000-0000-000000000001}
${RESOURCE_GROUP}          rg-example
${VM_NAME}                 vm-example
${EXPECTED_LOCATION}      westeurope
${EXPECTED_SIZE}          Standard_B2s
${EXPECTED_ENVIRONMENT}    test

*** Test Cases ***
VM Exists And Has Expected Configuration
    ${vm}=    Azure VM Should Exist    ${RESOURCE_GROUP}    ${VM_NAME}
    Should Be Equal    ${vm}[name]    ${VM_NAME}
    Azure VM Property Should Be    ${RESOURCE_GROUP}    ${VM_NAME}    location    ${EXPECTED_LOCATION}
    Azure VM Property Should Be    ${RESOURCE_GROUP}    ${VM_NAME}    vm_size    ${EXPECTED_SIZE}

VM Has Expected Environment Tag
    Azure VM Should Have Tag
    ...    ${RESOURCE_GROUP}    ${VM_NAME}    environment    ${EXPECTED_ENVIRONMENT}

VM Is Running
    Azure VM Power State Should Be    ${RESOURCE_GROUP}    ${VM_NAME}    running

VM Reaches Running State
    Wait Until Azure VM Power State Is
    ...    ${RESOURCE_GROUP}    ${VM_NAME}    running    timeout=120    poll_interval=5

VM Provisioning Succeeded
    ${vm}=    Get Azure VM    ${RESOURCE_GROUP}    ${VM_NAME}
    Should Be Equal    ${vm}[provisioning_state]    Succeeded
