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
