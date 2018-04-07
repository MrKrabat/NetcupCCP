#!/usr/bin/env python3
# coding: utf8

# Copyright (C) 2018 MrKrabat
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import copy


RR_ALLOWED_TYPES = ["A", "AAAA", "MX", "TXT", "CNAME", "SRV", "NS", "DS", "TLSA", "CAA"]


class CCPDomain(object):
    """
    Class holding all informations of a domain
    """

    def __init__(self, domain_id, domain_name, domain_zone, domain_serial, domain_dnssec=True, domain_webhosting=False):
        """
        Creates domain object
        """

        # check if domain_dnssec is bool
        if not isinstance(domain_dnssec, bool) and not domain_dnssec is None:
            raise TypeError("domain_dnssec of type bool or None expected")
        # check if domain_webhosting is bool
        if not isinstance(domain_webhosting, bool):
            raise TypeError("domain_webhosting of type bool expected")

        self.__id         = str(domain_id)
        self.__name       = str(domain_name)
        self.__zone       = str(domain_zone)
        self.__serial     = str(domain_serial)
        self.__dnssec     = domain_dnssec
        self.__webhosting = domain_webhosting
        self.__changed    = False
        self.__newcount   = 0
        self.__rr         = {}


    def getAllRecords(self):
        """
        Returns dict containing all resource records
        """

        return copy.deepcopy(self.__rr)


    def getRecord(self, rr_id):
        """
        Returns resource record for id
        """

        if rr_id in self.__rr:
            return copy.deepcopy(self.__rr[rr_id])
        else:
            return False


    def setRecord(self, rr_id, rr_host=None, rr_type=None, rr_destination=None, rr_pri=None):
        """
        Sets resource record data for existing entry
        """

        # check if rr_type allowed
        if rr_type and not rr_type in RR_ALLOWED_TYPES:
            raise ValueError("Not supported resource record")
        # check if id exists
        if not self.getRecord(rr_id):
            return False

        # update values
        self.__changed = True
        if rr_host:
            self.__rr[rr_id]["host"] = rr_host

        if rr_type:
            self.__rr[rr_id]["type"] = rr_type

        if rr_pri:
            self.__rr[rr_id]["pri"] = rr_pri

        if rr_destination:
            self.__rr[rr_id]["destination"] = rr_destination

        return True


    def addRecord(self, rr_host, rr_type, rr_destination, rr_pri=0, rr_id=None):
        """
        Creates new resource record
        """

        # check if rr_type allowed
        if not rr_type in RR_ALLOWED_TYPES:
            raise ValueError("Not supported resource record")

        new_id = False
        if not rr_id:
            new_id = "new[" + str(self.__newcount) + "]"
            self.__rr[new_id] = {"host": rr_host, "type": rr_type, "pri": rr_pri, "destination": rr_destination}
            self.__newcount += 1
        else:
            new_id = rr_id
            self.__rr[rr_id] = {"host": rr_host, "type": rr_type, "pri": rr_pri, "destination": rr_destination}

        self.__changed = True
        return new_id


    def removeRecord(self, rr_id):
        """
        Removes resource record
        """

        if "new[" in rr_id:
            # delete new enty
            self.__rr.pop(rr_id, False)
        else:
            # delete entry on server
            self.__rr[rr_id]["delete"] = rr_id[7:-1]

        self.__changed = True
        return True


    def getDNSSEC(self):
        """
        Returns domain dnssec state
        """

        return self.__dnssec


    def setDNSSEC(self, state):
        """
        Sets domain dnssec state
        """

        # check if state is bool
        if not isinstance(state, bool):
            raise TypeError("state of type bool expected")

        self.__changed = True
        self.__dnssec = state
        return True


    def searchRecord(self, rr_host, rr_type):
        """
        Returns all matching records
        """

        # check if rr_type allowed
        if not rr_type in RR_ALLOWED_TYPES:
            raise ValueError("Not supported resource record")

        ret = {}
        for key, value in self.__rr.items():
            if value["host"] == rr_host and value["type"] == rr_type:
                ret[key] = copy.deepcopy(value)

        return ret


    def getDomainID(self):
        """
        Returns domain id
        """

        return self.__id


    def getDomainName(self):
        """
        Returns domain name
        """

        return self.__name


    def getDomainZone(self):
        """
        Returns domain zone id
        """

        return self.__zone


    def getDomainSerial(self):
        """
        Returns last domain serial
        """

        return self.__serial


    def setDomainSerial(self, domain_serial):
        """
        Sets new domain serial
        """

        self.__serial = str(domain_serial)
        return True


    def isWebhosting(self):
        """
        Returns True if is webhosting domain
        """

        return self.__webhosting


    def hasChanged(self):
        """
        Returns True if domain object changed and needs to be saved
        """

        return self.__changed
