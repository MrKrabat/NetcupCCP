#!/usr/bin/env sh

# Copyright (C) 2018 MrKrabat
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Wrapper for Letsencrypt acme.sh client
# save this file in ./acme.sh/dnsapi/dns_netcup.sh
# set absolute paths to certbot_dns_* below
# command: acme.sh --issue -d example.com -d *.example.com --dns dns_netcup

# set environment variables
export CERTBOT_DOMAIN=$2
export CERTBOT_VALIDATION=$3

# deploy challenge
dns_netcup_add() {
    python3 certbot_dns_authenticator.py
}

# cleanup
dns_netcup_rm() {
    python3 certbot_dns_cleanup.py
}
