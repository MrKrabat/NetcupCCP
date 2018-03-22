#!/usr/bin/env python3
# coding: utf8

# Copyright (C) 2018 MrKrabat
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''
This package contains a python3 API for netcup dns settings.
'''

try:
    from ccp import CCPConnection
    from exception import *
except ImportError:
    from .ccp import CCPConnection
    from .exception import *
