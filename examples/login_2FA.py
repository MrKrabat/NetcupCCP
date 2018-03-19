#!/usr/bin/env python3
#
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

import pyotp # pyotp module required
import netcup


# 2FA generator
totp = pyotp.TOTP("<2FA private Token>")

# connect to cpp
ccp = netcup.CCPConnection(cachepath="mysession")
ccp.start(username  = "<CCP LOGIN>",
          password  = "<CCP PASSWORD>",
          token_2FA = totp.now())

# print all domains and keys
for key, value in ccp.getAllDomains().items():
    print(key + ": " + value)

# cleanup
ccp.close()
