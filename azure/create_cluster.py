##!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse

from joblib import Parallel, delayed

import utils
from utils import RG_TEMPLATE, STORAGE_ACCOUNT_TEMPLATE, VNET_NAME, SUBNET_NAME, NSG_NAME, region_by_user, \
    cloud_init_fill_template

parser = argparse.ArgumentParser()
parser.add_argument("--user", action="store", help="account name, for example student1", required=True)
parser.add_argument("--ssh_key", action="store", help="ssh public key, for example ~/.ssh/id_rsa_azure.pub",
                    required=False)
parser.add_argument("--create_shared", action="store_true", help="create shared resources")
parser.add_argument("--create_aux", action="store_true", help="create aux resources, only once per script run")
args = parser.parse_args()

student_name = args.user
rg_name = RG_TEMPLATE.format(student_name)
storage_account = STORAGE_ACCOUNT_TEMPLATE.format(student_name)
region = region_by_user[student_name]

RESIZE_OS_DISK = False
OS_DISK_SIZE = 511

if args.create_shared:
    utils.create_shared(rg_name, region)


def create_cluster_node(idx):
    IP_NAME = "ip_cluster{0}".format(idx)
    NIC_NAME = "nic_cluster{0}".format(idx)
    INT_DNS_NAME = "cluster{0}".format(idx)
    OS_DISK_NAME = "cluster{0}_os_disk".format(idx)
    VM_NAME = INT_DNS_NAME
    IP = "10.0.1.2{0}".format(idx)

    if idx != 1:
        IP_NAME = None

    if args.create_aux:
        # create public IP
        if IP_NAME is not None:
            utils.create_public_ip(IP_NAME, rg_name)

        # Create network card with fixed private IP
        utils.create_nic_with_private_ip(NIC_NAME, rg_name, VNET_NAME, SUBNET_NAME, NSG_NAME, IP_NAME, INT_DNS_NAME, IP)

    # create VM https://docs.microsoft.com/en-us/azure/virtual-machines/virtual-machines-windows-sizes
    VM_SIZE = "Standard_DS12_v2_Promo"
    pub_key = args.ssh_key

    IMAGE_NAME = "/subscriptions/" + utils.get_subscription_id() + \
                 "/resourceGroups/admin_resources/providers/Microsoft.Compute/images/" + \
                 "cluster{0}".format(idx) + "_image1_" + region
    data_disks = "1023"

    user_pass = utils.generate_pass()
    if idx == 1:
        cloud_init_fn = cloud_init_fill_template("configs/cloud_init_cluster_master_template.txt", user_pass)
    else:
        cloud_init_fn = "configs/cloud_init_cluster_slave.txt"
    utils.create_vm(VM_NAME, rg_name, region, IMAGE_NAME, NIC_NAME, VM_SIZE, pub_key, OS_DISK_NAME,
                    user_pass, cloud_init_fn, data_disks, "Premium_LRS")

    if RESIZE_OS_DISK:
        utils.deallocate_vm(VM_NAME, rg_name)
        utils.resize_managed_disk(rg_name, OS_DISK_NAME, OS_DISK_SIZE)
        utils.start_vm(VM_NAME, rg_name)

    print "password:", user_pass


Parallel(n_jobs=3, backend="threading")(
    delayed(create_cluster_node)(idx) for idx in [1, 2, 3]
)

print "cluster1 public IP: {}".format(utils.get_public_ip("ip_cluster1", rg_name))
