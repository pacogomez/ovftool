#!/usr/bin/python

__author__ = 'pacogomez'

from pyVim import connect
from pyVmomi import vim
import requests
import ssl
import atexit

def connect_to_nsx_api(ip, user, password, ssl_verify):
    appliance_check_url = 'https://{}/api/2.0/services/vcconfig'.format(ip)
    response = requests.request('GET', appliance_check_url,
                                auth=(user, password),
                                verify=ssl_verify)
    if response.status_code == 200:
        return True
    else:
        raise Exception('response: {}'.format(response.status_code))

def connect_to_vcenter_api(vc_host, vc_user, vc_pwd, ssl_verify):
    if hasattr(ssl, 'SSLContext'):
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.verify_mode = ssl.CERT_NONE
    else:
        context = None
    if ssl_verify:
        service_instance = connect.SmartConnect(host=vc_host, user=vc_user, pwd=vc_pwd)
    else:
        service_instance = connect.SmartConnect(host=vc_host, user=vc_user, pwd=vc_pwd, sslContext=context)
        
    atexit.register(connect.Disconnect, service_instance)
    return service_instance.RetrieveContent()

def main():
    module = AnsibleModule(
        argument_spec=dict(
            ip=dict(required=True, type='str'),
            user=dict(required=True, type='str'),
            password=dict(required=False, type='str', no_log=True),
            max_seconds=dict(required=False, type='int', default=True),
            service_type=dict(required=False, type='str', default='vcenter'),
            ssl_verify=dict(required=False, type='bool', default=True),
        ),
        supports_check_mode=True,
    )
    status_poll_count = 0
    sleep_time = 1
    while status_poll_count < module.params['max_seconds']:
        try:
            if module.params['service_type'] == 'vcenter':
                content = connect_to_vcenter_api(module.params['ip'],
                                                 module.params['user'],
                                                 module.params['password'],
                                                 module.params['ssl_verify'])
            elif module.params['service_type'] == 'nsx':
                content = connect_to_nsx_api(module.params['ip'],
                                             module.params['user'],
                                             module.params['password'],
                                             module.params['ssl_verify'])
            else:
                module.fail_json(changed=False, msg='unknown service {}'.format(module.params['service_type']))
            break
        except vim.fault.InvalidLogin:
            module.fail_json(msg='exception while connecting to service {}, login failure, check username and password'.format(module.params['service_type']))
        except:
            status_poll_count += 1
            time.sleep(sleep_time)

    if status_poll_count == module.params['max_seconds']:
        module.fail_json(changed=False, msg='timeout')
    else:
        module.exit_json(changed=False, msg='success')


from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
