# -*- coding: utf-8 -*-
# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
# Author: Chmouel Boudjnah <chmouel@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import datetime
import logging
import time

import dateutil.relativedelta
import swiftclient
import pyrax

import cloudfilesswiftsync as swsync
from cloudfilesswiftsync import get_config


class Accounts(object):
    """Process Keystone Accounts."""
    def __init__(self):
        self.keystone_cnx = None
        self.container_cls = swsync.containers.Containers()

    def get_swift_auth(self, auth_url, tenant, user, password):
        """Get swift connexion from args."""
        return swiftclient.client.Connection(
            auth_url,
            '%s:%s' % (tenant, user),
            password,
            auth_version=2).get_auth()

    def get_cloudfiles_auth_orig(self):
        """Get cloudfiles cnx from config."""
        cfg = get_config('auth', 'cloudfiles_origin_credentials')
        (username, apikey, region) = cfg.split(':')

        pyrax.set_setting('identity_type',  'rackspace')

        pyrax.set_credentials(username,apikey,region)

        return pyrax

    def sync_account(self):
        """Sync a single account with url/tok to dest_url/dest_tok."""

        import pydevd
        pydevd.settrace('localhost', port=53100, stdoutToServer=True, stderrToServer=True)

        orig_storage_cnx = self.get_cloudfiles_auth_orig()
        dest_auth_url = get_config('auth', 'keystone_dest')

        cfg = get_config('auth', 'keystone_dest')
        (orig_user, orig_password, orig_tenant) = cfg.split(':')

        dest_storage_url = get_config('auth', 'dest_storage_url')

        # we assume orig and dest passwd are the same obv synchronized.
        dst_st_url, dest_token = self.get_swift_auth(
            dest_auth_url, orig_tenant,
            orig_user, orig_password)
        dest_storage_cnx = swiftclient.http_connection(dest_storage_url)

        try:
            orig_containers = orig_storage_cnx.cloudfiles.list_containers()
            dest_account_headers, dest_containers = (
                swiftclient.get_account(None, dest_token,
                                        http_conn=dest_storage_cnx,
                                        full_listing=True))
        except(swiftclient.client.ClientException), e:
                logging.info("error getting account: %s" % (
                     e.http_reason))
                return

        container_list = iter(orig_containers)
        if cloudfilesswiftsync.utils.REVERSE:
            container_list = reversed(orig_containers)

        for container in container_list:
            logging.info("Syncronizing container %s: %s",
                         container['name'], container)
            dt1 = datetime.datetime.fromtimestamp(time.time())
            self.container_cls.sync(orig_storage_cnx,
                                    dest_storage_cnx,
                                    dest_storage_url, dest_token,
                                    container['name'])

            dt2 = datetime.datetime.fromtimestamp(time.time())
            rd = dateutil.relativedelta.relativedelta(dt2, dt1)
            # TODO(chmou): use logging
            logging.info("%s done: %d hours, %d minutes and %d seconds",
                         container['name'],
                         rd.hours,
                         rd.minutes, rd.seconds)


def main():
    acc = Accounts()
    acc.sync_account()
