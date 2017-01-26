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
            vm_name=dict(required=True, type='str'),
            vcenter=dict(required=True, type='str'),
            vcenter_user=dict(required=True, type='str'),
            vcenter_password=dict(required=True, type='str', no_log=True),
            datacenter=dict(required=True, type='str'),
            cluster=dict(required=True, type='str'),
            datastore=dict(required=True, type='str'),
            portgroup=dict(required=True, type='str'),
            path_to_ova=dict(required=True, type='str'),
            ova_file=dict(required=True, type='str'),
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
                                                   module.params['vcenter_password'], module.params['vcenter'],
                                                   module.params['datacenter'], module.params['cluster'])

    ova_tool_result = module.run_command([ovftool_exec,
                                          '--acceptAllEulas',
                                          '--skipManifestCheck',
                                          '--powerOn',
                                          '--noSSLVerify',
                                          '--allowExtraConfig',
                                          # '--diskMode={}'.format(module.params['disk_mode']),
                                          '--datastore={}'.format(module.params['datastore']),
                                          # TODO: specify network to map
                                          '--network={}'.format(module.params['portgroup']),
                                          '--name={}'.format(module.params['vm_name']),
                                          # '--prop:vsm_hostname={}'.format(module.params['hostname']),
                                          # '--prop:vsm_dns1_0={}'.format(module.params['dns_server']),
                                          # '--prop:vsm_domain_0={}'.format(module.params['dns_domain']),
                                          # '--prop:vsm_ntp_0={}'.format(module.params['ntp_server']),
                                          # '--prop:vsm_gateway_0={}'.format(module.params['gateway']),
                                          # '--prop:vsm_ip_0={}'.format(module.params['ip_address']),
                                          # '--prop:vsm_netmask_0={}'.format(module.params['netmask']),
                                          # '--prop:vsm_cli_passwd_0={}'.format(module.params['admin_password']),
                                          # '--prop:vsm_cli_en_passwd_0={}'.format(module.params['enable_password']),
                                          ova_file, 
                                          vi_string])

    if ova_tool_result[0] != 0:
        module.fail_json(msg='Failed to deploy OVA, error message from ovftool is: {}'.format(ova_tool_result[1]))
    # if not wait_for_api(module):
    #     module.fail_json(msg='Failed to deploy OVA, timed out waiting for the API to become available')

    module.exit_json(changed=True, ova_tool_result=ova_tool_result)


from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()