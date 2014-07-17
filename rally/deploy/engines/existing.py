# Copyright 2013: Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from rally import consts
from rally.deploy import engine
from rally import objects


class ExistingCloud(engine.EngineFactory):
    """ExistingCloud doesn't deploy OpenStack it just use existing.

       To use ExistingCloud you should put in a config endpoint key, e.g:

            {
                "type": "ExistingCloud",
                "endpoint": {
                    "auth_url": "http://localhost:5000/v2.0/",
                    "username": "admin",
                    "password": "password",
                    "tenant_name": "demo",
                    "region_name": "RegionOne",
                    "use_public_urls": False,
                    "keystone_admin_port": 35357
                }
            }

    """

    CONFIG_SCHEMA = {
        'type': 'object',
        'properties': {
            'type': {'type': 'string'},
            'endpoint': {
                'type': 'object',
                'properties': {
                    'auth_url': {'type': 'string'},
                    'username': {'type': 'string'},
                    'password': {'type': 'string'},
                    'tenant_name': {'type': 'string'},
                    'region_name': {'type': 'string'},
                    'use_public_urls': {'type': 'boolean'},
                    'admin_port': {
                        'type': 'integer',
                        'minimum': 2,
                        'maximum': 65535
                    }
                },
                'required': ['auth_url', 'username', 'password',
                             'tenant_name'],
            },
        },
        'required': ['type', 'endpoint'],
    }

    def deploy(self):
        endpoint_dict = self.deployment['config']['endpoint']
        admin_endpoint = objects.Endpoint(endpoint_dict['auth_url'],
                                          endpoint_dict['username'],
                                          endpoint_dict['password'],
                                          endpoint_dict['tenant_name'],
                                          consts.EndpointPermission.ADMIN,
                                          endpoint_dict.get('region_name'),
                                          endpoint_dict.get('use_public_urls',
                                                            False),
                                          endpoint_dict.get('admin_port',
                                                            35357))
        return [admin_endpoint]

    def cleanup(self):
        pass
