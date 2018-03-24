#!/usr/bin/env python3
# coding: utf8

# Copyright (C) 2018 MrKrabat
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from certbot_dns_authenticator import *


# cleanup dns key
if __name__ == "__main__":
    # find dns entry
    for key, value in mydomain.searchRecord(rr_host=DOMAIN_HOST, rr_type="TXT").items():
        if value["destination"] == CERTBOT_VALIDATION:
            mydomain.removeRecord(key)
            break

    # save changes
    ccp.saveDomain(mydomain)

    # cleanup
    ccp.close()

    # wait 10 seconds for changes to take effect
    time.sleep(10)
