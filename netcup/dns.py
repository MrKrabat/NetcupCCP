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

import re
import gzip
from bs4 import BeautifulSoup
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode
try:
    from urllib2 import urlopen, build_opener, HTTPCookieProcessor, install_opener
except ImportError:
    from urllib.request import urlopen, build_opener, HTTPCookieProcessor, install_opener
try:
    from cookielib import LWPCookieJar
except ImportError:
    from http.cookiejar import LWPCookieJar

try:
    from domain import CCPDomain
    from exception import *
except ImportError:
    from .domain import CCPDomain
    from .exception import *


class CCPConnection(object):
    """
    Netcup CCP API
    """

    def __init__(self, cachepath=None, debug=False):
        """
        Creates CCP connection
        """
        self._cache = False
        self._sessionhash = None
        self._nocsrftoken = None
        self._debug = debug

        # creates urllib with custom headers and cookie management
        self._jar = LWPCookieJar()
        self._network = build_opener(HTTPCookieProcessor(self._jar))
        self._network.addheaders = [("User-Agent",      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299"),
                                    ("Accept-Encoding", "gzip, deflate, br"),
                                    ("Accept",          "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8")]

        # load session cache from disk
        if cachepath:
            self._cache = True
            self._cachepath = cachepath
            # load cookies
            try:
                self._jar.load(cachepath, ignore_discard=True)
                self._log("Loaded cache successful")
            except IOError:
                # cookie file does not exist
                self._log("Could not load cache, maybe does not exists yet")


    def start(self, username, password):
        """
        Performs login if session is invalid
        """

        # validate cached session
        if self._cache:
            resource = self._network.open("https://ccp.netcup.net/run/domains.php")
            content = gzip.decompress(resource.read()).decode(resource.headers.get_content_charset())
            if username in content:
                self._log("Session still valid")
                self.__getTokens(content)
                return True
            else:
                self._log("Session has expired")

        # create login post
        payload = {"action":       "login",
                   "nocsrftoken":  "",
                   "ccp_user":     username,
                   "ccp_password": password,
                   "language":     "DE",
                   "login":        "Login / Anmelden"}
        payload = urlencode(payload)

        # send login
        resource = self._network.open("https://ccp.netcup.net/run/start.php", payload.encode("utf-8"))
        content = gzip.decompress(resource.read()).decode(resource.headers.get_content_charset())

        # check if login successful
        if username in content:
            resource = self._network.open("https://ccp.netcup.net/run/domains.php")
            content = gzip.decompress(resource.read()).decode(resource.headers.get_content_charset())

            self._log("Login successful")
            self.__getTokens(content)
            return True
        else:
            raise NetcupLoginError()


    def close(self):
        """
        Save session or perform logout
        """

        # check if caching is enabled
        if self._cache:
            # save session
            self._log("Saving session to disk")
            self._jar.save(self._cachepath, ignore_discard=True)
        else:
            # logout
            self._log("Performing logout")
            self._network.open("https://ccp.netcup.net/run/logout.php")


    def getAllDomains(self, search="", page=1):
        """
        Returns dict containing domain id and name
        """

        # get domain list
        resource = self._network.open("https://ccp.netcup.net/run/domains_ajax.php?suchstrg=" + search + "&action=listdomains&seite=" + str(page) + "&sessionhash=" + self._sessionhash + "&nocsrftoken=" + self._nocsrftoken)
        content = gzip.decompress(resource.read()).decode(resource.headers.get_content_charset())
        self.__getTokens(content)
        self._log("Received domain list")

        # parse list
        id = re.findall(r"showDomainsDetails\((.*?)\);", content)
        name = re.findall(r"<td>([a-zA-Z0-9-_\.äöüß]+?)\s", content)
        ret = {}

        # generate response
        for i in range(len(id)):
            ret[id[i]] = name[i]

        return ret


    def getDomain(self, id):
        """
        Return Domain object
        """

        # get domain info
        resource = self._network.open("https://ccp.netcup.net/run/domains_ajax.php?domain_id=" + str(id) + "&action=showdomainsdetails&sessionhash=" + self._sessionhash + "&nocsrftoken=" + self._nocsrftoken)
        content = gzip.decompress(resource.read()).decode(resource.headers.get_content_charset())
        self.__getTokens(content)
        self._log("Received domain details")

        # parse html
        soup = BeautifulSoup(content, "html.parser")
        div = soup.find("div", {"id": "domainsdetail_detail_dns_" + str(id)})
        table = div.find_all("table")

        # table[0] contains Zone/Serial/DNSSEC state
        dnssec = True if "checked" in str(div.find("input", {"id": "dnssecenabled_" + str(id)})) else False
        domain = CCPDomain(id=id,
                           name=div.find("input", {"name": "zone"}).get("value"),
                           zone=div.find("input", {"name": "zoneid"}).get("value"),
                           serial=div.find("input", {"name": "serial"}).get("value"),
                           dnssec=dnssec)

        # for very dns entry
        for row in table[1].find_all("tr")[1:-2]:
            column = row.find_all("td")

            # get values
            host = column[0].input.get("value")
            pri = column[2].input.get("value")
            destination = column[3].input.get("value")
            type = "Error"
            for option in column[1].find_all("option"):
                if option.get("selected"):
                    type = option.get("value")
                    break

            # if record contain values
            if host:
                domain.addRecord(host, type, destination, pri, column[0].input.get("name")[:-6])

        return domain


    def saveDomain(self, id, domain):
        """
        Saves domain object on netcup
        """

        # create post payload
        payload = {"dnssecenabled":              str(not domain.getDNSSEC()).lower(),
                   "zone":                       domain._name,
                   "zoneid":                     domain._zone,
                   "serial":                     domain._serial,
                   "order":                      "",
                   "formchanged":                "",
                   "restoredefaults_" + str(id): "false",
                   "submit":                     "DNS Records speichern"}

        # add dns records to payload
        for key, value in domain.getAllRecords().items():
            payload[key + "[host]"] = value["host"]
            payload[key + "[type]"] = value["type"]
            payload[key + "[pri]"] = value["pri"]
            payload[key + "[destination]"] = value["destination"]
            if "delete" in value:
                payload[key + "[delete]"] = value["delete"]

        # send update
        payload = urlencode(payload)
        resource = self._network.open("https://ccp.netcup.net/run/domains_ajax.php?action=editzone&domain_id=" + str(id) + "&sessionhash=" + self._sessionhash + "&nocsrftoken=" + self._nocsrftoken,
                                      payload.encode("utf-8"))
        content = gzip.decompress(resource.read()).decode(resource.headers.get_content_charset())
        self.__getTokens(content)
        self._log("DNS records saved")
        return True


    def __getTokens(self, html):
        """
        Retrieves session and csrf token
        """
        try:
            self._sessionhash = re.search(r"sessionhash = \"(.*?)\";", html).group(1)
            self._log("sessionhash: " + self._sessionhash)
        except AttributeError:
            pass

        try:
            self._nocsrftoken = re.search(r"nocsrftoken = \"(.*?)\";", html).group(1)
            self._log("nocsrftoken: " + self._nocsrftoken)
        except AttributeError:
            try:
                self._nocsrftoken = re.search(r"nocsrftoken = '(.*?)';", html).group(1)
                self._log("nocsrftoken: " + self._nocsrftoken)
            except AttributeError:
                pass


    def __getNewCSRF(self):
        """
        Gets new csrf token from api
        """

        # request token
        resource = self._network.open("https://ccp.netcup.net/run/nocrfs_ajax.php?&action=getnocsrftoken&sessionhash=" + self._sessionhash)
        self._nocsrftoken = gzip.decompress(resource.read()).decode(resource.headers.get_content_charset())
        self._log("nocsrftoken: " + self._nocsrftoken)


    def _log(self, msg):
        """
        Prints debug messages
        """
        if self._debug:
            print(msg)
