#!/usr/bin/env python3
# coding: utf8

# Copyright (C) 2018 MrKrabat
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


class CCPError(Exception):
    """
    This is the base class for all exceptions in this package
    """
    pass


class CCPLoginError(CCPError):
    """
    Raised, if login failed
    """
    pass


class CCPSessionExpired(CCPError):
    """
    Raised, if session expired
    """
    pass


class CCPWebsiteChanges(CCPError):
    """
    Raised, if website parsing failed
    """
    pass


class CCPSaveDomainError(CCPError):
    """
    Raised, if failed to save domain
    """
    pass
