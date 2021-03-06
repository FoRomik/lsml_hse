#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess

import pandas as pd

from utils import RG_TEMPLATE, STORAGE_ACCOUNT_TEMPLATE, region_by_user, check_output_wrapper

users = pd.read_json("users.json", orient="records")

for idx, (_, row) in enumerate(users.iterrows()):
    # if idx + 1 <= 88:
    #     continue
    row = dict(row)
    user = row["user"]
    # if user != "student54":
    #     continue
    userId = row["userId"]
    rgName = RG_TEMPLATE.format(user)
    region = region_by_user[user]
    # create res gr
    print "start", user
    check_output_wrapper(
        """
        az group create \
        -n "{n}" \
        -l "{l}"
        """.format(n=rgName, l=region),
        shell=True
    )
    # assign user to his res gr
    check_output_wrapper(
        """
        az role assignment create \
        --assignee {userId} \
        --role Contributor \
        --resource-group {rg}
        """.format(userId=userId, rg=rgName),
        shell=True
    )
    # create storage account
    storName = STORAGE_ACCOUNT_TEMPLATE.format(user)
    check_output_wrapper(
        """
        az storage account create \
        -l {l} \
        -n {n} \
        -g {g} \
        --sku Standard_LRS
        """.format(l=region, n=storName, g=rgName),
        shell=True
    )
    print(user, "done")
