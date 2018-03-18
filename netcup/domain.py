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


class CCPDomain(object):
    """
    Class holding all informations of a domain
    """

    def __init__(self, id, name, zone, serial, dnssec=True):
        """
        Creates domain object
        """

        self._id = id
        self._name = name
        self._zone = zone
        self._serial = serial
        self._dnssec = dnssec
        self._changed = False
        self._newcount = 0
        self._rr = {}


    def getAllRecords(self):
        """
        Returns dict containing all resource records
        """

        return self._rr


    def getRecord(self, id):
        """
        Returns resource record for id
        """

        return self._rr.get(id, False)


    def setRecord(self, id, host, type, destination, pri=0):
        """
        Sets resource record data for existing entry
        """

        # check if id exists
        if not self.getRecord(id):
            return False

        # update values
        self._changed = True
        self._rr[id]["host"] = host
        self._rr[id]["type"] = type
        self._rr[id]["pri"] = pri
        self._rr[id]["destination"] = destination
        return True


    def addRecord(self, host, type, destination, pri=0, id=None):
        """
        Creates new resource record
        """

        if not id:
            self._rr["new[" + str(self._newcount) + "]"] = {"host": host, "type": type, "pri": pri, "destination": destination}
            self._newcount += 1
        else:
            self._rr[id] = {"host": host, "type": type, "pri": pri, "destination": destination}

        return True


    def removeRecord(self, id):
        """
        Removes resource record
        """

        if "new[" in id:
            # delete new enty
            self._rr.pop(id, False)
        else:
            # delete entry on server
            self._rr[id]["delete"] = id[7:-1]

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


    def searchRecord(self, host, type):
        """
        Returns all matching records
        """

        ret = {}
        for key, value in self._rr.items():
            if value["host"] == host and value["type"] == type:
                ret[key] = value

        return ret
