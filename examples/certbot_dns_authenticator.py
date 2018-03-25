#!/usr/bin/env python3
# coding: utf8

# Copyright (C) 2018 MrKrabat
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import time

import netcup

'''
Certbot command:
certbot certonly --manual --preferred-challenges=dns --manual-auth-hook authenticator.py --manual-cleanup-hook cleanup.py -d *.domain.tld -d domain.tld

- chmod +x for both scripts
- Paths to the hooks have to be absolute
- Wildcard certificates require certbot 0.22
- Wildcard certificates requere ACMEv2, add argument --server https://acme-v02.api.letsencrypt.org/directory
- It takes approximately 10 minutes per domain for verifying
- Will only work if all domains in CSR are from one netcup account
'''

# certbot arguments
CERTBOT_DOMAIN  = os.environ["CERTBOT_DOMAIN"]
CERTBOT_VALIDATION = os.environ["CERTBOT_VALIDATION"]

# connect to cpp
ccp = netcup.CCPConnection(cachepath="mysession")
ccp.start(username = "<CCP LOGIN>",
          password = "<CCP PASSWORD>")

# get domain_id
for key, value in ccp.getDomainList(search=".".join(CERTBOT_DOMAIN.split(".")[-2:])).items():
    if value in CERTBOT_DOMAIN:
        DOMAIN_ID = key
        DOMAIN_NAME = value
        break

# check if domain_id found
if not DOMAIN_ID:
    raise Exception("Could not find domain in ccp")

# get hostname
if DOMAIN_NAME == CERTBOT_DOMAIN or "*." + DOMAIN_NAME == CERTBOT_DOMAIN:
    DOMAIN_HOST = "_acme-challenge"
elif DOMAIN_NAME in CERTBOT_DOMAIN:
    DOMAIN_HOST = "_acme-challenge." + CERTBOT_DOMAIN[:-(len(DOMAIN_NAME)+1)]
else:
    # failed to generate hostname
    raise Exception("Could not get Hostname")

# get domain infos
mydomain = ccp.getDomain(DOMAIN_ID)

# deploy dns key
if __name__ == "__main__":
    # add acme challenge
    mydomain.addRecord(rr_host        = DOMAIN_HOST,
                       rr_type        = "TXT",
                       rr_destination = CERTBOT_VALIDATION)

    # save changes
    ccp.saveDomain(mydomain)

    # wait for changes to take effect
    timer = time.time() + 15*60
    while True:
        time.sleep(60)
        # check if settings are live or timeout reached
        if ccp.isRecordLive(DOMAIN_ID) or time.time() > timer:
            break

    # cleanup
    ccp.close()
