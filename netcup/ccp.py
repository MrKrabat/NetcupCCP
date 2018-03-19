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

from re import search, findall
from bs4 import BeautifulSoup
from gzip import decompress
from base64 import b64encode
from urllib.parse import urlencode, quote_plus
from urllib.request import build_opener, HTTPCookieProcessor
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

    def __init__(self, cachepath=None):
        """
        Creates CCP connection
        """
        self._cache = False
        self._sessionhash = None
        self._nocsrftoken = None

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
            except IOError:
                # cookie file does not exist
                pass


    def start(self, username, password, token_2FA=None):
        """
        Performs login if session is invalid
        """

        # validate cached session
        if self._cache:
            resource = self._network.open("https://ccp.netcup.net/run/domains.php")
            content = decompress(resource.read()).decode(resource.headers.get_content_charset())
            if username in content:
                self.__getTokens(content)
                return True

        # create login post
        payload = {"action":       "login",
                   "nocsrftoken":  "",
                   "ccp_user":     username,
                   "ccp_password": password,
                   "language":     "DE",
                   "login":        "Login / Anmelden"}

        # 2FA Auth
        if token_2FA:
            payload.pop("ccp_password", False)
            payload["pwdb64"] = b64encode(password.encode("ascii"))
            payload["tan"] = str(token_2FA)

        # send login
        payload = urlencode(payload)
        resource = self._network.open("https://ccp.netcup.net/run/start.php", payload.encode("utf-8"))
        content = decompress(resource.read()).decode(resource.headers.get_content_charset())

        # check if login successful
        if username in content:
            resource = self._network.open("https://ccp.netcup.net/run/domains.php")
            content = decompress(resource.read()).decode(resource.headers.get_content_charset())
            self.__getTokens(content)

            if not self._sessionhash or not self._nocsrftoken:
                raise NetcupLoginError()

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
            self._jar.save(self._cachepath, ignore_discard=True)
        else:
            # logout
            self._network.open("https://ccp.netcup.net/run/logout.php")


    def getDomainList(self, search="", page=1):
        """
        Returns dict containing domain id and name
        """

        # get domain list
        resource = self._network.open("https://ccp.netcup.net/run/domains_ajax.php?suchstrg=" + quote_plus(search) + "&action=listdomains&seite=" + str(page) + "&sessionhash=" + self._sessionhash + "&nocsrftoken=" + self._nocsrftoken)
        content = decompress(resource.read()).decode(resource.headers.get_content_charset())
        self.__getTokens(content)

        # parse list
        domain_id = findall(r"showDomainsDetails\((.*?)\);", content)
        domain_name = findall(r"<td>([a-zA-Z0-9-_\.äöüß]+?)\s", content)
        ret = {}

        # generate response
        for i in range(len(domain_id)):
            ret[domain_id[i]] = domain_name[i]

        return ret


    def getDomain(self, domain_id):
        """
        Return Domain object
        """

        # get domain info
        resource = self._network.open("https://ccp.netcup.net/run/domains_ajax.php?domain_id=" + str(domain_id) + "&action=showdomainsdetails&sessionhash=" + self._sessionhash + "&nocsrftoken=" + self._nocsrftoken)
        content = decompress(resource.read()).decode(resource.headers.get_content_charset())
        self.__getTokens(content)

        # parse html
        soup = BeautifulSoup(content, "html.parser")
        div = soup.find("div", {"id": "domainsdetail_detail_dns_" + str(domain_id)})
        table = div.find_all("table")

        # table[0] contains Zone/Serial/DNSSEC state
        dnssec = True if "checked" in str(div.find("input", {"id": "dnssecenabled_" + str(domain_id)})) else False
        domain_obj = CCPDomain(domain_id     = domain_id,
                               domain_name   = div.find("input", {"name": "zone"}).get("value"),
                               domain_zone   = div.find("input", {"name": "zoneid"}).get("value"),
                               domain_serial = div.find("input", {"name": "serial"}).get("value"),
                               domain_dnssec = dnssec)

        # for very dns entry
        for row in table[1].find_all("tr")[1:-2]:
            column = row.find_all("td")

            # get values
            rr_host = column[0].input.get("value")
            rr_pri = column[2].input.get("value")
            rr_destination = column[3].input.get("value")
            rr_type = "Error"
            for option in column[1].find_all("option"):
                if option.get("selected"):
                    rr_type = option.get("value")
                    break

            # if record contain values
            if rr_host:
                domain_obj.addRecord(rr_host, rr_type, rr_destination, rr_pri, column[0].input.get("name")[:-6])

        return domain_obj


    def saveDomain(self, domain_obj):
        """
        Saves domain object on netcup
        """

        # check if object changed
        if not domain_obj._changed:
            return True

        # create post payload
        payload = {"dnssecenabled": str(not domain_obj.getDNSSEC()).lower(),
                   "zone":          domain_obj._name,
                   "zoneid":        domain_obj._zone,
                   "serial":        domain_obj._serial,
                   "order":         "",
                   "formchanged":   "",
                   "restoredefaults_" + str(domain_obj._id): "false",
                   "submit":        "DNS Records speichern"}

        # add dns records to payload
        for key, value in domain_obj.getAllRecords().items():
            payload[key + "[host]"] = value["host"]
            payload[key + "[type]"] = value["type"]
            payload[key + "[pri]"]  = value["pri"]
            payload[key + "[destination]"] = value["destination"]
            if "delete" in value:
                payload[key + "[delete]"] = value["delete"]

        # send update
        payload = urlencode(payload)
        resource = self._network.open("https://ccp.netcup.net/run/domains_ajax.php?action=editzone&domain_id=" + str(domain_obj._id) + "&sessionhash=" + self._sessionhash + "&nocsrftoken=" + self._nocsrftoken,
                                      payload.encode("utf-8"))
        content = decompress(resource.read()).decode(resource.headers.get_content_charset())
        self.__getTokens(content)
        return True


    def isRecordLive(self, domain_id):
        """
        Checks if domain dns records are live
        """

        # get domain info
        resource = self._network.open("https://ccp.netcup.net/run/domains_ajax.php?domain_id=" + str(domain_id) + "&action=showdomainsdetails&sessionhash=" + self._sessionhash + "&nocsrftoken=" + self._nocsrftoken)
        content = decompress(resource.read()).decode(resource.headers.get_content_charset())
        self.__getTokens(content)

        if "<td>yes</td>" in content:
            return True
        else:
            return False


    def __getTokens(self, html):
        """
        Retrieves session and csrf token
        """
        try:
            self._sessionhash = search(r"sessionhash = \"(.*?)\";", html).group(1)
        except AttributeError:
            pass

        try:
            self._nocsrftoken = search(r"nocsrftoken = \"(.*?)\";", html).group(1)
        except AttributeError:
            try:
                self._nocsrftoken = search(r"nocsrftoken = '(.*?)';", html).group(1)
            except AttributeError:
                pass


    def __getNewCSRF(self):
        """
        Gets new csrf token from api
        """

        # request token
        resource = self._network.open("https://ccp.netcup.net/run/nocrfs_ajax.php?&action=getnocsrftoken&sessionhash=" + self._sessionhash)
        self._nocsrftoken = decompress(resource.read()).decode(resource.headers.get_content_charset())
