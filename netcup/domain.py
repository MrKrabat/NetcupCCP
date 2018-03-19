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

import copy


class CCPDomain(object):
    """
    Class holding all informations of a domain
    """

    def __init__(self, domain_id, domain_name, domain_zone, domain_serial, domain_dnssec=True):
        """
        Creates domain object
        """

        self._id = domain_id
        self._name = domain_name
        self._zone = domain_zone
        self._serial = domain_serial
        self._dnssec = domain_dnssec
        self._changed = False
        self._newcount = 0
        self._rr = {}


    def getAllRecords(self):
        """
        Returns dict containing all resource records
        """

        return copy.deepcopy(self._rr)


    def getRecord(self, rr_id):
        """
        Returns resource record for id
        """

        if rr_id in self._rr:
            return copy.deepcopy(self._rr[rr_id])
        else:
            return False


    def setRecord(self, rr_id, rr_host=None, rr_type=None, rr_destination=None, rr_pri=None):
        """
        Sets resource record data for existing entry
        """

        # check if id exists
        if not self.getRecord(rr_id):
            return False

        # update values
        self._changed = True
        if rr_host:
            self._rr[rr_id]["host"] = rr_host

        if rr_type:
            self._rr[rr_id]["type"] = rr_type

        if rr_pri:
            self._rr[rr_id]["pri"] = rr_pri

        if rr_destination:
            self._rr[rr_id]["destination"] = rr_destination

        return True


    def addRecord(self, rr_host, rr_type, rr_destination, rr_pri=0, rr_id=None):
        """
        Creates new resource record
        """

        if not rr_id:
            self._rr["new[" + str(self._newcount) + "]"] = {"host": rr_host, "type": rr_type, "pri": rr_pri, "destination": rr_destination}
            self._newcount += 1
        else:
            self._rr[rr_id] = {"host": rr_host, "type": rr_type, "pri": rr_pri, "destination": rr_destination}

        self._changed = True
        return True


    def removeRecord(self, rr_id):
        """
        Removes resource record
        """

        if "new[" in rr_id:
            # delete new enty
            self._rr.pop(rr_id, False)
        else:
            # delete entry on server
            self._rr[rr_id]["delete"] = rr_id[7:-1]

        self._changed = True
        return True


    def getDNSSEC(self):
        """
        Returns domain dnssec state
        """

        return self._dnssec


    def setDNSSEC(self, state):
        """
        Sets domain dnssec state
        """

        self._changed = True
        self._dnssec = state
        return True


    def searchRecord(self, rr_host, rr_type):
        """
        Returns all matching records
        """

        ret = {}
        for key, value in self._rr.items():
            if value["host"] == rr_host and value["type"] == rr_type:
                ret[key] = value

        return ret
