#!/usr/bin/env python3
# coding: utf8

# Copyright (C) 2018 MrKrabat
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
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
        self.__cache = False
        self.__sessionhash = None
        self.__nocsrftoken = None

        # creates urllib with custom headers and cookie management
        self.__jar = LWPCookieJar()
        self.__network = build_opener(HTTPCookieProcessor(self.__jar))
        self.__network.addheaders = [("User-Agent",      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299"),
                                     ("Accept-Encoding", "gzip, deflate, br"),
                                     ("Accept",          "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8")]

        # load session cache from disk
        if cachepath:
            # check if path is writeable
            path = os.path.dirname(cachepath)
            if not path:
                path = "."

            if not os.access(path, os.W_OK):
                raise IOError("cachepath is not writeable")

            self.__cache = True
            self.__cachepath = cachepath
            # load cookies
            try:
                self.__jar.load(cachepath, ignore_discard=True)
            except IOError:
                # cookie file does not exist
                pass


    def start(self, username, password, token_2FA=None):
        """
        Performs login if session is invalid
        """

        # check if arguments are strings
        if not isinstance(username, str):
            username = str(username)
        if not isinstance(password, str):
            password = str(password)
        if token_2FA and not isinstance(token_2FA, str):
            token_2FA = str(token_2FA)

        # validate cached session
        if self.__cache:
            resource = self.__network.open("https://ccp.netcup.net/run/domains.php")
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
            payload["tan"]    = token_2FA

        # send login
        payload = urlencode(payload)
        resource = self.__network.open("https://ccp.netcup.net/run/start.php", payload.encode("utf-8"))
        content = decompress(resource.read()).decode(resource.headers.get_content_charset())

        # check if login successful
        if username in content:
            resource = self.__network.open("https://ccp.netcup.net/run/domains.php")
            content = decompress(resource.read()).decode(resource.headers.get_content_charset())
            self.__getTokens(content)

            # check tokens
            if not self.__sessionhash or not self.__nocsrftoken:
                if token_2FA:
                    raise CCPLoginError("2FA token invalid")
                else:
                    raise CCPLoginError("Your account has 2FA enabled")

            return True
        else:
            raise CCPLoginError("Login failed check your credentials")


    def close(self):
        """
        Save session or perform logout
        """

        # check if caching is enabled
        if self.__cache:
            # save session
            self.__jar.save(self.__cachepath, ignore_discard=True)
        else:
            # logout
            resource = self.__network.open("https://ccp.netcup.net/run/logout.php")
            content = decompress(resource.read()).decode(resource.headers.get_content_charset())


    def getDomainList(self, search="", page=1):
        """
        Returns dict containing domain id and name
        """

        # get domain list
        resource = self.__network.open("https://ccp.netcup.net/run/domains_ajax.php?suchstrg=" + quote_plus(search) + "&action=listdomains&seite=" + str(page) + "&sessionhash=" + self.__sessionhash + "&nocsrftoken=" + self.__nocsrftoken)
        content = decompress(resource.read()).decode(resource.headers.get_content_charset())
        self.__getTokens(content)

        # check if domains found
        if "Es wurden keine Domains zu ihrer Suche nach" in content or "Sie haben keine Domains gebucht" in content:
            return {}

        # parse list
        domain_id = findall(r"showDomainsDetails\((.*?)\);", content)
        domain_name = findall(r"<td>([a-zA-Z0-9-_\.äöüß]+?)\s", content)

        # check result
        if not domain_id or not domain_name:
            raise CCPWebsiteChanges("Could not find domains and keys")
        # check if len equals
        if not len(domain_id) == len(domain_name):
            raise CCPWebsiteChanges("Number of domains does not match number of keys")

        # return dict
        return dict(zip(domain_id, domain_name))


    def getDomain(self, domain_id):
        """
        Return Domain object
        """

        # get domain info
        resource = self.__network.open("https://ccp.netcup.net/run/domains_ajax.php?domain_id=" + str(domain_id) + "&action=showdomainsdetails&sessionhash=" + self.__sessionhash + "&nocsrftoken=" + self.__nocsrftoken)
        content = decompress(resource.read()).decode(resource.headers.get_content_charset())
        self.__getTokens(content)

        # parse html
        soup = BeautifulSoup(content, "html.parser")
        div = soup.find("div", {"id": "domainsdetail_detail_dns_" + str(domain_id)})
        if not div:
            raise CCPWebsiteChanges("Could not get DNS tab")

        table = div.find_all("table")
        if not table:
            raise CCPWebsiteChanges("Could not get RR table")

        # create CCPDomain object
        try:
            webhosting = True if "restoredefaultslabel_" + str(domain_id) in str(div) else False
            dnssec = True if "checked" in str(div.find("input", {"id": "dnssecenabled_" + str(domain_id)})) else None
            domain_obj = CCPDomain(domain_id         = domain_id,
                                   domain_name       = div.find("input", {"name": "zone"}).get("value"),
                                   domain_zone       = div.find("input", {"name": "zoneid"}).get("value"),
                                   domain_serial     = div.find("input", {"name": "serial"}).get("value"),
                                   domain_dnssec     = dnssec,
                                   domain_webhosting = webhosting,
                                   domain_ttl        = div.find("input", {"name": "zone_settings_ttl_" + str(domain_id)}).get("value"),
                                   domain_retry      = div.find("input", {"name": "zone_settings_retry_" + str(domain_id)}).get("value"),
                                   domain_expire     = div.find("input", {"name": "zone_settings_expire_" + str(domain_id)}).get("value"),
                                   domain_refresh    = div.find("input", {"name": "zone_settings_refresh_" + str(domain_id)}).get("value"))
        except (AttributeError, TypeError) as e:
            raise CCPWebsiteChanges("Could not get domain infos")

        # for every dns entry
        del_lines = -2 if not webhosting else -4
        for row in table[-2].find_all("tr")[1:del_lines]:
            column = row.find_all("td")

            # get values
            try:
                rr_host = column[0].input.get("value")
                rr_pri = column[2].input.get("value")
                rr_destination = column[3].input.get("value")
                rr_type = ""

                for option in column[1].find_all("option"):
                    if option.get("selected"):
                        rr_type = option.get("value")
                        break
            except (AttributeError, TypeError, KeyError) as e:
                raise CCPWebsiteChanges("Could not get RR row")

            # if record contain values
            if rr_host:
                domain_obj.addRecord(rr_host, rr_type, rr_destination, rr_pri, column[0].input.get("name")[:-6])

        return domain_obj


    def saveDomain(self, domain_obj):
        """
        Saves domain object on netcup
        """

        # check if domain_obj is CCPDomain
        if not isinstance(domain_obj, CCPDomain):
            raise TypeError("Object of type CCPDomain expected")

        # check if object changed
        if not domain_obj.hasChanged():
            return True

        # create post payload
        payload = {"zone":          domain_obj.getDomainName(),
                   "zoneid":        domain_obj.getDomainZone(),
                   "serial":        domain_obj.getDomainSerial(),
                   "order":         "",
                   "formchanged":   "",
                   "zone_settings_ttl_"     + domain_obj.getDomainID(): domain_obj.getTTL(),
                   "zone_settings_expire_"  + domain_obj.getDomainID(): domain_obj.getExpire(),
                   "zone_settings_retry_"   + domain_obj.getDomainID(): domain_obj.getRetry(),
                   "zone_settings_refresh_" + domain_obj.getDomainID(): domain_obj.getRefresh(),
                   "restoredefaults_"       + domain_obj.getDomainID(): "false",
                   "submit":        "DNS Records speichern"}

        # set dnssec state
        if isinstance(domain_obj.getDNSSEC(), bool):
            payload["dnssecenabled"] = str(not domain_obj.getDNSSEC()).lower()

        # add dns records to payload
        for key, value in domain_obj.getAllRecords().items():
            try:
                payload[key + "[host]"] = value["host"]
                payload[key + "[type]"] = value["type"]
                payload[key + "[pri]"]  = value["pri"]
                payload[key + "[destination]"] = value["destination"]
                if "delete" in value:
                    payload[key + "[delete]"] = value["delete"]
            except KeyError:
                raise ValueError("Invalid CCPDomain object")

        # send update
        payload = urlencode(payload)
        resource = self.__network.open("https://ccp.netcup.net/run/domains_ajax.php?action=editzone&domain_id=" + domain_obj.getDomainID() + "&sessionhash=" + self.__sessionhash + "&nocsrftoken=" + self.__nocsrftoken,
                                      payload.encode("utf-8"))
        content = decompress(resource.read()).decode(resource.headers.get_content_charset())
        self.__getTokens(content)

        # check if update was successful
        if not "Eintrag erfolgreich!" in content:
            raise CCPSaveDomainError("Could not save domain")

        # parse html
        soup = BeautifulSoup(content, "html.parser")
        try:
            # update domain serial
            domain_obj.setDomainSerial(soup.find("input", {"name": "serial"}).get("value"))
        except (AttributeError, TypeError) as e:
            raise CCPWebsiteChanges("Could not get domain serial")

        return True


    def isRecordLive(self, domain_id):
        """
        Checks if domain dns records are live
        """

        # get domain info
        resource = self.__network.open("https://ccp.netcup.net/run/domains_ajax.php?domain_id=" + str(domain_id) + "&action=showdomainsdetails&sessionhash=" + self.__sessionhash + "&nocsrftoken=" + self.__nocsrftoken)
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

        # check session
        if "Your session has expired" in html:
            raise CCPSessionExpired("CCP session expired")

        try:
            self.__sessionhash = search(r"sessionhash = \"(.*?)\";", html).group(1)
        except AttributeError:
            pass

        try:
            self.__nocsrftoken = search(r"nocsrftoken = \"(.*?)\";", html).group(1)
        except AttributeError:
            try:
                self.__nocsrftoken = search(r"nocsrftoken = '(.*?)';", html).group(1)
            except AttributeError:
                self.__getNewCSRF()


    def __getNewCSRF(self):
        """
        Gets new csrf token from api
        """

        # request token
        resource = self.__network.open("https://ccp.netcup.net/run/nocrfs_ajax.php?&action=getnocsrftoken&sessionhash=" + self.__sessionhash)
        self.__nocsrftoken = decompress(resource.read()).decode(resource.headers.get_content_charset())

        if "Your session has expired" in self.__nocsrftoken:
            raise CCPSessionExpired("CCP session expired")
