#!/usr/bin/python

__author__ = 'pacogomez'

from pyVim import connect
from pyVmomi import vim
import requests
import ssl
import atexit

def connect_to_api(vchost, vc_user, vc_pwd):
    if hasattr(ssl, 'SSLContext'):
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.verify_mode = ssl.CERT_NONE
    else:
        context = None
    if context:
        service_instance = connect.SmartConnect(host=vchost, user=vc_user, pwd=vc_pwd, sslContext=context)
    else:
        service_instance = connect.SmartConnect(host=vchost, user=vc_user, pwd=vc_pwd)
    atexit.register(connect.Disconnect, service_instance)
    return service_instance.RetrieveContent()

def get_all_objs(content, vimtype):
    obj = {}
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for managed_object_ref in container.view:
        obj.update({managed_object_ref: managed_object_ref.name})
    return obj

def find_virtual_machine(content, vm_name):
    virtual_machines = get_all_objs(content, [vim.VirtualMachine])
    for vm in virtual_machines:
        if vm.name == vm_name:
            return vm
    return None

def main():
    module = AnsibleModule(
        argument_spec=dict(
            ovftool_path=dict(required=True, type='str'),
            vcenter=dict(required=True, type='str'),
            vcenter_user=dict(required=True, type='str'),
            vcenter_password=dict(required=True, type='str', no_log=True),
            datacenter=dict(required=True, type='str'),
            cluster=dict(required=True, type='str'),
            datastore=dict(required=True, type='str'),
            portgroup=dict(required=True, type='str'),
            disk_mode=dict(required=False, type='str', default='thin'),
            path_to_ova=dict(required=True, type='str'),
            ova_file=dict(required=True, type='str'),
            vm_name=dict(required=True, type='str'),
            vm_password_key=dict(required=False, type='str'),
            vm_password=dict(required=False, type='str', no_log=True),
            power_on=dict(required=False, type='bool', default=True),
            ssl_verify=dict(required=False, type='bool', default=True),
            props=dict(required=False, type='dict'),
        ),
        supports_check_mode=True,
    )
    try:
        content = connect_to_api(module.params['vcenter'], module.params['vcenter_user'],
                                 module.params['vcenter_password'])
    except vim.fault.InvalidLogin:
        module.fail_json(msg='exception while connecting to vCenter, login failure, check username and password')
    except requests.exceptions.ConnectionError:
        module.fail_json(msg='exception while connecting to vCenter, check hostname, FQDN or IP')
    
    target_vm = find_virtual_machine(content, module.params['vm_name'])

    if target_vm:
        module.fail_json(msg='A VM with the name {} is already present'.format(module.params['vm_name']))

    ovftool_exec = '{}/ovftool'.format(module.params['ovftool_path'])
    ova_file = '{}/{}'.format(module.params['path_to_ova'], module.params['ova_file'])
    vi_string = 'vi://{}:{}@{}/{}/host/{}/'.format(module.params['vcenter_user'],
                                                   module.params['vcenter_password'],
                                                   module.params['vcenter'],
                                                   module.params['datacenter'],
                                                   module.params['cluster'])
    
    command_tokens = [ovftool_exec,
                      '--acceptAllEulas',
                      '--skipManifestCheck']
    if module.params['power_on']:
        command_tokens.append('--powerOn')
    if not module.params['ssl_verify']:
        command_tokens.append('--noSSLVerify')
    command_tokens.extend([
                      '--allowExtraConfig',
                      '--diskMode={}'.format(module.params['disk_mode']),
                      '--datastore={}'.format(module.params['datastore']),
                      # TODO: specify the network to map
                      '--network={}'.format(module.params['portgroup']),
                      '--name={}'.format(module.params['vm_name']),])
    if module.params['props']:
        for key in module.params['props'].keys():
            command_tokens.append('--prop:{}={}'.format(key, module.params['props'][key]))
    if 'vm_password_key' in module.params and 'vm_password' in module.params:
        command_tokens.append('--prop:{}={}'.format(module.params['vm_password_key'], module.params['vm_password']))
    command_tokens.extend([ova_file, vi_string])

    ova_tool_result = module.run_command(command_tokens)
    
    # module.exit_json(changed=False, command=command_tokens)

    # ova_tool_result = module.run_command([ovftool_exec,
    #                                       '--acceptAllEulas',
    #                                       '--skipManifestCheck',
    #                                       '--powerOn',
    #                                       '--noSSLVerify',
    #                                       '--allowExtraConfig',
    #                                       '--diskMode={}'.format(module.params['disk_mode']),
    #                                       '--datastore={}'.format(module.params['datastore']),
    #                                       # TODO: specify the network to map
    #                                       '--network={}'.format(module.params['portgroup']),
    #                                       '--name={}'.format(module.params['vm_name']),
    #                                       '--prop:guestinfo.hostname={}'.format(module.params['vm_name']),
    #                                       '--prop:guestinfo.ipaddress={}'.format('10.158.13.200'),
    #                                       '--prop:guestinfo.netmask={}'.format('255.255.252.0'),
    #                                       '--prop:guestinfo.gateway={}'.format('10.158.15.253'),
    #                                       '--prop:guestinfo.password={}'.format(module.params['vm_password']),
    #                                       ova_file,
    #                                       vi_string])
    #
    if ova_tool_result[0] != 0:
        module.fail_json(msg='Failed to deploy OVA, error message from ovftool is: {}'.format(ova_tool_result[1]))
    # # if not wait_for_api(module):
    # #     module.fail_json(msg='Failed to deploy OVA, timed out waiting for the API to become available')
    #
    module.exit_json(changed=True, ova_tool_result=ova_tool_result)


from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
