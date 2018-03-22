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

# print all domains and keys
for key, value in ccp.getDomainList().items():
    print(key + ": " + value)

# cleanup
ccp.close()
