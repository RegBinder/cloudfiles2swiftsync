#!/usr/bin/python
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

import setuptools

from cloudfilesswiftsync import openstack

name = 'cloudfilesswiftsync'

requires = openstack.setup.parse_requirements()
depend_links = openstack.setup.parse_dependency_links()
entry_point = '%s.middlewares:last_modified' % (name)


setuptools.setup(
    name=name,
    version=openstack.setup.get_version(name),
    description='A sync objects from Rackspace Cloud Files to a Swift cluster',
    url='https://github.com/RegBinder/cloudfiles2swiftsync',
    license='Apache License (2.0)',
    author='Complion Inc',
    author_email='info@complion.com',
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    cmdclass=openstack.setup.get_cmdclass(),
    install_requires=requires,
    dependency_links=depend_links,
    classifiers=[
        'Development Status :: 1 - Alpha',
        'Environment :: Console',
        'Environment :: OpenStack',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Environment :: No Input/Output (Daemon)',
    ],
    scripts=[
        'bin/cloudfilesswiftsyncer',
    ],
    entry_points={
        'paste.filter_factory': ['last_modified=%s' % entry_point]
    }
)
