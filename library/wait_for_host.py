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

def main():
    module = AnsibleModule(
        argument_spec=dict(
            ip=dict(required=True, type='str'),
            user=dict(required=True, type='str'),
            password=dict(required=False, type='str', no_log=True),
            max_seconds=dict(required=False, type='int', default=True),
            ssl_verify=dict(required=False, type='bool', default=True),
        ),
        supports_check_mode=True,
    )
    status_poll_count = 0
    sleep_time = 1
    while status_poll_count < module.params['max_seconds']:
        try:
            content = connect_to_api(module.params['ip'], module.params['user'],
                                     module.params['password'])
            break
        except vim.fault.InvalidLogin:
            module.fail_json(msg='exception while connecting to vCenter, login failure, check username and password')
        except:
            status_poll_count += 1
            time.sleep(sleep_time)

    if status_poll_count == 120:
        module.fail_json(changed=False, msg='timeout')
    else:
        module.exit_json(changed=False, msg='success')


from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
