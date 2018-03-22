#!/usr/bin/env python3
# coding: utf8

# Copyright (C) 2018 MrKrabat
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import netcup


# connect to cpp
ccp = netcup.CCPConnection(cachepath="mysession")
ccp.start(username = "<CCP LOGIN>",
          password = "<CCP PASSWORD>")

# get domain infos
mydomain = ccp.getDomain("<DOMAIN ID>")

# add record
mydomain.addRecord(rr_host        = "demo",
                   rr_type        = "A",
                   rr_destination = "127.0.0.1")

# save changes
ccp.saveDomain(mydomain)

# cleanup
ccp.close()
