# -*- coding: utf-8 -*-
# Copyright (C) 2015 Complion Inc <info@complion.com>
#
# Part of this work was borrowed from Chmouel Boudjnah <chmouel@enovance.com>
# Author: Greg Svitak <greg@complion.com>
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
import logging

import eventlet
import swiftclient
import cloudfilesswiftsync

from cloudfilesswiftsync import utils
from cloudfilesswiftsync import objects


class Containers(object):
    """Containers sync."""
    def __init__(self):
        self.concurrency = int(utils.get_config(
                               "concurrency",
                               "sync_swift_client_concurrency"))
        self.sync_object = cloudfilesswiftsync.objects.sync_object
        self.delete_object = cloudfilesswiftsync.objects.delete_object

    def delete_container(self, dest_storage_cnx, dest_token,
                         orig_containers,
                         dest_containers):
        set1 = set((x['name']) for x in orig_containers)
        set2 = set((x['name']) for x in dest_containers)
        delete_diff = set2 - set1

        pool = eventlet.GreenPool(size=self.concurrency)
        pile = eventlet.GreenPile(pool)
        for container in delete_diff:
            try:
                dest_container_stats, dest_objects = swiftclient.get_container(
                    None, dest_token, container, http_conn=dest_storage_cnx,
                    full_listing=True,
                )
            except(swiftclient.client.ClientException), e:
                logging.info("error getting container: %s, %s" % (
                    container, e.http_reason))
                continue

            for obj in dest_objects:
                logging.info("deleting obj: %s ts:%s", obj['name'],
                             obj['last_modified'])
                pile.spawn(self.delete_object,
                           dest_storage_cnx,
                           dest_token,
                           container,
                           obj['name'])
            pool.waitall()
            logging.info("deleting container: %s", container)
            pile.spawn(swiftclient.delete_container,
                       '', dest_token, container, http_conn=dest_storage_cnx)
        pool.waitall()

    def container_headers_clean(self, container_headers, to_null=False):
        ret = {}
        for key, value in container_headers.iteritems():
            if key.startswith('x-container-meta'):
                if to_null:
                    value = ''
                ret[key] = value
        return ret

    def sync(self, orig_storage_cnx, dest_storage_cnx, dest_storage_url, dest_token,
             orig_container):

        try:
            container_headers = orig_container.get_metadata()
            orig_container_headers = orig_container.get_metadata()
            orig_objects = orig_container.get_objects(full_listing=True)
            #marker = ""
            #objs = orig_container.get_objects(limit=100, marker=marker)
            # orig_container_headers = orig_container.get_metadata()
            # orig_objects = []
            # for obj in objs:
            #     while objs:
            #         marker = obj.name
            #         orig_objects.append(obj)
            #         objs = orig_container.get_objects(limit=100, marker=marker)
        except(swiftclient.client.ClientException), e:
            logging.info("ERROR: getting container: %s, %s" % (
                orig_container.name, e.http_reason))
            return

        try:
            # Check that the container exists on dest
            swiftclient.head_container(
                "", dest_token, orig_container.name,  http_conn=dest_storage_cnx
            )
        except(swiftclient.client.ClientException), e:

            orig_container_headers = container_headers
            for h in ('x-container-object-count', 'x-trans-id',
                      'x-container-bytes-used'):
                try:
                    del container_headers[h]
                except KeyError:
                    # Nov2013: swift server does not set x-trans-id header
                    pass
            p = dest_storage_cnx[0]
            url = "%s://%s%s" % (p.scheme, p.netloc, p.path)
            try:
                swiftclient.put_container(url,
                                          dest_token, orig_container.name,
                                          headers=container_headers)
            except(swiftclient.client.ClientException), e:
                logging.info("ERROR: creating container: %s, %s" % (
                    orig_container.name, e.http_reason))
                return

        try:
            dest_container_headers, dest_objects = swiftclient.get_container(
                dest_storage_url, dest_token, orig_container.name, http_conn=dest_storage_cnx,
                full_listing=True,
            )
        except(swiftclient.client.ClientException), e:
            logging.info("ERROR: creating container: %s, %s" % (
                orig_container.name, e.http_reason))
            return

        try:
            header_key = 'x-container-meta-last-modified'
            orig_ts = float(container_headers[header_key])
            dest_ts = float(dest_container_headers[header_key])
            if orig_ts < dest_ts:
                logging.info("Dest is up-to-date")
                return
        except(KeyError):
            # last-modified swift middleware is not active
            pass
        except(ValueError):
            logging.error("Could not decode last-modified header!")

        do_headers = False
        if len(dest_container_headers) != len(container_headers):
            do_headers = True
        else:
            for k, v in container_headers.iteritems():
                if (k.startswith('x-container-meta') and
                        k in dest_container_headers):
                    if dest_container_headers[k] != v:
                        do_headers = True

        if do_headers:
            orig_metadata_headers = self.container_headers_clean(
                orig_container_headers)
            dest_metadata_headers = self.container_headers_clean(
                dest_container_headers, to_null=True)
            new_headers = dict(dest_metadata_headers.items() +
                               orig_metadata_headers.items())
            try:
                swiftclient.post_container(
                    "", dest_token, orig_container.name, new_headers,
                    http_conn=dest_storage_cnx,
                )
                logging.info("HEADER: sync headers: %s" % (orig_container.name))
            except(swiftclient.client.ClientException), e:
                logging.info("ERROR: updating container metadata: %s, %s" % (
                    orig_container.name, e.http_reason))
                # We don't pass on because since the server was busy
                # let's pass it on for the next pass
                return
        set1 = set((x._info['last_modified'], x.name) for x in orig_objects)

        set2 = set((x['last_modified'], x['name']) for x in dest_objects)
        diff = set1 - set2
        set1 = set(x.name for x in orig_objects)
        set2 = set(x['name'] for x in dest_objects)
        delete_diff = set2 - set1

        if not diff and not delete_diff:
            return

        pool = eventlet.GreenPool(size=self.concurrency)
        pile = eventlet.GreenPile(pool)

        for obj in orig_objects:
            logging.info("sending: %s ts:%s", obj.container, obj.name)
            pile.spawn(self.sync_object,
                       orig_storage_cnx,
                       orig_container,
                       dest_storage_url,
                       dest_token, orig_container.name,
                       obj)

        # for obj in delete_diff:
        #     logging.info("deleting: %s ts:%s", obj[1], obj[0])
        #     pile.spawn(self.delete_object,
        #                dest_storage_cnx,
        #                dest_token,
        #                orig_container.name,
        #                obj)
        pool.waitall()
