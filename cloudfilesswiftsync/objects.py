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
import urllib
import psycopg2.extras
import textwrap
import urllib2

import eventlet
import swift.common.bufferedhttp
import swift.common.http

try:
    from swift.container.sync import _Iter2FileLikeObject as FileLikeIter
except ImportError:
    # Nov2013: swift.common.utils now include a more generic object
    from swift.common.utils import FileLikeIter
from swiftclient import client as swiftclient


def quote(value, safe='/'):
    """Patched version of urllib.quote.

    Encodes utf-8 strings before quoting.
    """
    if isinstance(value, unicode):
        value = value.encode('utf-8')
    return urllib.quote(value, safe)


def get_object(
        orig_container,
        object_name):
    response_timeout = 15

    with eventlet.Timeout(response_timeout):
        resp_headers, obj = orig_container.fetch_object(object_name, include_meta=True)

    return (resp_headers, obj)


def delete_object(dest_cnx,
                  dest_token,
                  container_name,
                  object_name):
    parsed = dest_cnx[0]
    url = '%s://%s/%s' % (parsed.scheme, parsed.netloc, parsed.path)
    swiftclient.delete_object(url=url,
                              token=dest_token,
                              container=container_name,
                              http_conn=dest_cnx,
                              name=object_name)


def sync_object(orig_storage_cnx, orig_container, dest_storage_url,
                dest_token, container_name, obj, postges_connection):
    object_name = obj.name

    orig_headers, orig_body = get_object(orig_container,
                                         object_name)
    container_name = quote(container_name)

    post_headers = orig_headers
    post_headers['x-auth-token'] = dest_token
    sync_to = dest_storage_url + "/" + container_name
    try:
        swiftclient.put_object(sync_to, name=object_name,
                               headers=post_headers,
                               contents=FileLikeIter(orig_body))
        cursor = postges_connection.cursor()

        cursor.execute(textwrap.dedent("""
            insert into synced_objects
            (container_name, object_name)
            values
            (
                %(container_name)s,
                %(object_name)s
                )

            """),
           {'container_name': container_name, 'object_name': object_name})
        postges_connection.commit()

    except(swiftclient.ClientException), e:
        logging.info("error sync object: %s, %s" % (
            object_name, e.http_reason))

        cursor = postges_connection.cursor()

        cursor.execute(textwrap.dedent("""
            insert into error_objects
            (container_name, object_name, error_message)
            values
            (
                %(container_name)s,
                %(object_name)s,
                %(error_message)s
            )

            """),
                       {'container_name': container_name,
                        'object_name': object_name,
                        'error_message': "error sync object: %s, %s" % (
                            object_name, e.http_reason)
                        })
        postges_connection.commit()
