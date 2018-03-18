#!/usr/bin/env python3
# coding: utf8

# Copyright (C) 2018 MrKrabat
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import time

import netcup

"""
Certbot command:
certbot certonly --manual --preferred-challenges=dns --manual-auth-hook /root/certbot/authenticator.py --manual-cleanup-hook /root/certbot/cleanup.py -d *.domain.tld -d domain.tld
"""

def getNetcupDomain(fqdn):
    """
    Returns domainname for netcup ccp
    """
    for key, value in DOMAIN_LIST.items():
        if value == fqdn or "*." + value == fqdn:
            return "_acme-challenge"
        elif value in fqdn:
            return "_acme-challenge." + fqdn[:-(len(value)+1)]
            
            
def getDomainID(fqdn):
    """
    Returns domain id
    """
    for key, value in DOMAIN_LIST.items():
        if value in fqdn:
            return key


# start api connection
ccp = netcup.dns.CCPConnection(cachepath="/root/certbot/mysession")
ccp.start(username="<CCP NAME>", password="<CCP PASSWORD>")

# data
DOMAIN_LIST        = {"<DOMAIN ID>": "<DOMAIN NAME>", "<DOMAIN ID2>": "<DOMAIN NAME2>"}
DOMAIN_ID          = getDomainID(os.environ["CERTBOT_DOMAIN"])
CERTBOT_DOMAIN     = getNetcupDomain(os.environ["CERTBOT_DOMAIN"])
CERTBOT_VALIDATION = os.environ["CERTBOT_VALIDATION"]

# load domain data
mydomain = ccp.getDomain(DOMAIN_ID)

# add acme challenge
mydomain.addRecord(CERTBOT_DOMAIN, "TXT", CERTBOT_VALIDATION)

# save changes
ccp.saveDomain(DOMAIN_ID, mydomain)

# cleanup
ccp.close()

# wait 5 minutes for changes to take effect
time.sleep(5*60)
