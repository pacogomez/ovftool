
    source ~/prj/ansible/hacking/env-setup
    source ./env-setup


https://download3.vmware.com/software/vmw-tools/nested-esxi/Nested_ESXi6.x_Appliance_Template_v5.ova
https://download3.vmware.com/software/vmw-tools/nested-esxi/Nested_ESXi6.5_Appliance_Template_v1.ova

~/prj/ansible/hacking/test-module -m ./ovftool.py -a "ovftool_path=\"/Applications/VMware OVF Tool\" vcenter=10.158.13.196 vcenter_user=administrator@vsphere.local vcenter_password=${PASSWORD} vm_name=esx1 datacenter=dctr1 datastore=SAP-3TB-2 portgroup='VM Network' cluster=cluster1 path_to_ova=. ova_file=Nested_ESXi6.x_Appliance_Template_v5.ova"


Install the module:

    wget https://raw.githubusercontent.com/pacogomez/ansible-module-ovftool/master/ovftool.py