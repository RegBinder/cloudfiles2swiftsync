__author__ = 'gregsvitak'

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



import optparse
import sys

import complion.cloudfilesswiftsync.accounts
import complion.cloudfilesswiftsync.utils

class Main(object):
    def __init__(self):
        self.options = {}

    def main(self):
        usage = "usage: %prog [OPTIONS] [CONF_FILE]"
        parser = optparse.OptionParser(usage=usage)
        parser.add_option(
            '-l', '--log-level',
            dest='log_level',
            default='info',
            help='Number of containers to distribute objects among')
        parser.add_option(
            '-R', '--reverse',
            action="store_true",
            dest='reverse',
            default=False,
            help='Traverse container list forward or reversed')
        self.options, args = parser.parse_args()
        if self.options:
            complion.cloudfilesswiftsync.utils.REVERSE = self.options.reverse
        if args:
            conf = complion.cloudfilesswiftsync.utils.parse_ini(args[0])
        else:
            try:
                conf = complion.cloudfilesswiftsync.utils.parse_ini()
            except(complion.cloudfilesswiftsync.utils.ConfigurationError):
                parser.print_help()
                sys.exit(1)

        complion.cloudfilesswiftsync.utils.set_logging(self.options.log_level.lower())
        complion.cloudfilesswiftsync.utils.CONFIG = conf
        complion.cloudfilesswiftsync.accounts.main()

if __name__ == '__main__':
    m = Main()
    m.main()
