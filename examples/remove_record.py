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

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import netcup


# start api connection
ccp = netcup.dns.CCPConnection(cachepath="mysession", debug=False)
ccp.start(username="<CCP NAME>", password="<CCP PASSWORD>")

# get domains
domainlist = ccp.getAllDomains(search="", page=1)
    
# get infos of first domain
domainid = list(domainlist.keys())[0]
mydomain = ccp.getDomain(domainid)

# remove record(s)
for key, value in mydomain.searchRecord(host="demo", type="A").items():
    mydomain.removeRecord(key)

# save changes
ccp.saveDomain(domainid, mydomain)

# cleanup
ccp.close()
