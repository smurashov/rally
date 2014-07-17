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

import novaclient.exceptions
import os
import time
import urllib2

from rally.benchmark import utils as benchmark_utils
from rally.deploy.serverprovider import provider
from rally import exceptions
from rally.objects import endpoint
from rally.openstack.common.gettextutils import _
from rally.openstack.common import log as logging
from rally import osclients


LOG = logging.getLogger(__name__)


SERVER_TYPE = 'server'
KEYPAIR_TYPE = 'keypair'


class OpenStackProvider(provider.ProviderFactory):
    """Provides VMs using existing OpenStack cloud.

    Sample configuration:

    {
        "type": "OpenStackProvider",
        "amount": 42
        "user": "admin",
        "tenant": "admin",
        "password": "secret",
        "auth_url": "http://example.com/",
        "flavor_id": 2,
        "image": {
            "checksum": "75846dd06e9fcfd2b184aba7fa2b2a8d",
            "url": "http://example.com/disk1.img",
            "name": "Ubuntu Precise(added by rally)",
            "format": "qcow2",
            "userdata": "#cloud-config\r\n disable_root: false"
        }
    }

    """

    CONFIG_SCHEMA = {
        'type': 'object',
        'properties': {
            'type': {'type': 'string'},
            'deployment_name': {'type': 'string'},
            'amount': {'type': 'integer'},
            'user': {'type': 'string'},
            'nics': {'type': 'array'},
            'password': {'type': 'string'},
            'tenant': {'type': 'string'},
            'auth_url': {'type': 'string'},
            'flavor_id': {'type': 'string'},
            'image': {
                'type': 'object',
                'properties': {
                    'checksum': {'type': 'string'},
                    'name': {'type': 'string'},
                    'format': {'type': 'string'},
                    'userdata': {'type': 'string'},
                    'url': {'type': 'string'},
                    'uuid': {'type': 'string'},
                },
                'additionalProperties': False,
                'anyOf': [
                    {
                        'title': 'Create Image',
                        'required': ['name', 'format', 'url', 'checksum'],
                    },
                    {
                        'title': 'Existing image from checksum',
                        'required': ['checksum']
                    },
                    {
                        'title': 'Existing image from uuid',
                        'required': ['uuid']
                    }
                ]
            },
        },
        'additionalProperties': False,
        'required': ['user', 'password', 'tenant', 'deployment_name',
                     'auth_url', 'flavor_id', 'image']
    }

    def __init__(self, deployment, config):
        super(OpenStackProvider, self).__init__(deployment, config)
        user_endpoint = endpoint.Endpoint(config['auth_url'], config['user'],
                                          config['password'], config['tenant'])
        clients = osclients.Clients(user_endpoint)
        self.nova = clients.nova()
        try:
            self.glance = clients.glance()
        except KeyError:
            self.glance = None
            LOG.warning(_('Glance endpoint not available in service catalog'
                          ', only existing images can be used'))

    def get_image_uuid(self):
        """Get image uuid. Download image if necessary."""

        image_uuid = self.config['image'].get('uuid', None)
        if image_uuid:
            return image_uuid
        else:
            if not self.glance:
                raise exceptions.InvalidConfigException(
                    'If glance is not available in the service catalog'
                    ' obtained by the openstack server provider, then'
                    ' images cannot be uploaded so the uuid of an'
                    ' existing image must be specified in the'
                    ' deployment config.'
                )

        for image in self.glance.images.list():
            if image.checksum == self.config['image']['checksum']:
                LOG.info(_('Found image with appropriate checksum. Using it.'))
                return image.id

        LOG.info(_('Downloading new image %s') % self.config['image']['url'])
        image = self.glance.images.create(name=self.config['image']['name'])
        try:
            image.update(data=urllib2.urlopen(self.config['image']['url']),
                         disk_format=self.config['image']['format'],
                         container_format='bare')
        except urllib2.URLError:
            LOG.error(_('Unable to retrieve %s') % self.config['image']['url'])
            raise
        image.get()

        if image.checksum != self.config['image']['checksum']:
            raise exceptions.ChecksumMismatch(url=self.config['image']['url'])

        return image.id

    def get_userdata(self):
        userdata = self.config['image'].get('userdata', None)
        if userdata is not None:
            return userdata
        userdata = self.config['image'].get('userdata_file', None)
        if userdata is not None:
            userdata = open(userdata, 'r')
        return userdata

    def create_keypair(self):
        public_key_path = self.config.get(
            'ssh_public_key_file', os.path.expanduser('~/.ssh/id_rsa.pub'))
        public_key = open(public_key_path, 'r').read().strip()
        key_name = self.config['deployment_name'] + '-key'
        try:
            key = self.nova.keypairs.find(name=key_name)
            self.nova.keypairs.delete(key.id)
        except novaclient.exceptions.NotFound:
            pass
        keypair = self.nova.keypairs.create(key_name, public_key)
        self.resources.create({'id': keypair.id}, type=KEYPAIR_TYPE)
        return keypair, public_key_path

    def get_nics(self):
        return self.config.get("nics", None)

    def create_servers(self):
        """Create VMs with chosen image."""

        image_uuid = self.get_image_uuid()
        userdata = self.get_userdata()
        flavor = self.config['flavor_id']
        nics = self.get_nics()

        keypair, public_key_path = self.create_keypair()

        os_servers = []
        for i in range(self.config.get('amount', 1)):
            name = "%s-%d" % (self.config['deployment_name'], i)
            server = self.nova.servers.create(name, image_uuid, flavor,
                                              nics=nics,
                                              key_name=keypair.name,
                                              userdata=userdata)
            os_servers.append(server)
            self.resources.create({'id': server.id}, type=SERVER_TYPE)

        kwargs = {
            'is_ready': benchmark_utils.resource_is("ACTIVE"),
            'update_resource': benchmark_utils.get_from_manager(),
            'timeout': 120,
            'check_interval': 5
        }

        for os_server in os_servers:
            benchmark_utils.wait_for(os_server, **kwargs)
        servers = [provider.Server(host=s.addresses.values()[0][0]['addr'],
                                   user='root',
                                   key=public_key_path)
                   for s in os_servers]
        for s in servers:
            s.ssh.wait(timeout=120, interval=5)

        # NOTE(eyerediskin): usually ssh is ready much earlier then cloud-init
        time.sleep(8)
        return servers

    def destroy_servers(self):
        for resource in self.resources.get_all(type=SERVER_TYPE):
            try:
                self.nova.servers.delete(resource['info']['id'])
            except novaclient.exceptions.NotFound:
                LOG.warning(
                    "Nova Instance: %(id)s not found,"
                    " so not deleting." % dict(id=resource['info']['id'])
                )
            try:
                self.resources.delete(resource.id)
            except exceptions.ResourceNotFound:
                LOG.warning(
                    'Instance resource record not found in DB, not removing.'
                    ' Deployment: %(deploy_id)s Instance ID:%(id)s'
                    ' Instance Nova UUID:%(uuid)s' %
                    dict(deploy_id=resource.deployment_uuid,
                         id=resource.id,
                         uuid=resource['info']['id']
                         )
                )
        for resource in self.resources.get_all(type=KEYPAIR_TYPE):
            try:
                self.nova.keypairs.delete(resource['info']['id'])
            except novaclient.exceptions.NotFound:
                LOG.warning(
                    "Nova keypair: %(id)s not found,"
                    " so not deleting." % dict(id=resource['info']['id'])
                )
            try:
                self.resources.delete(resource.id)
            except exceptions.ResourceNotFound:
                LOG.warning(
                    'Keypair resource record not found in DB, not removing.'
                    ' Deployment: %(deploy_id)s Keypair ID:%(id)s'
                    ' Keypair Name:%(name)s' %
                    dict(deploy_id=resource.deployment_uuid,
                         id=resource.id,
                         name=resource['info']['id']
                         )
                )
