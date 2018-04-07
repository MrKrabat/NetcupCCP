#!/usr/bin/env sh

# Copyright (C) 2018 MrKrabat
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Wrapper for Letsencrypt acme.sh client
# save this file in ./acme.sh/dnsapi/dns_netcup.sh
# set absolute paths to certbot_dns_* below
# command: acme.sh --issue -d example.com -d *.example.com --dns dns_netcup --dnssleep 0


# deploy challenge
dns_netcup_add() {
    # set environment variables
    export CERTBOT_DOMAIN=`echo "$1" | sed 's/_acme-challenge.//'`
    export CERTBOT_VALIDATION=$2

    python3 /root/certbot/certbot_dns_authenticator.py
}

# cleanup
dns_netcup_rm() {
    # set environment variables
    export CERTBOT_DOMAIN=`echo "$1" | sed 's/_acme-challenge.//'`
    export CERTBOT_VALIDATION=$2

    python3 /root/certbot/certbot_dns_cleanup.py
}
