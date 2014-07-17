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

import mock
import multiprocessing
import uuid

from glanceclient import exc
from novaclient import exceptions
from rally.benchmark.context import base as base_ctx
from rally.benchmark.scenarios import base
from rally.objects import endpoint
from rally import utils as rally_utils


def generate_uuid():
    return str(uuid.uuid4())


class FakeResource(object):

    def __init__(self, manager=None, name=None, status="ACTIVE", items=None,
                 deployment_uuid=None, id=None):
        self.name = name or generate_uuid()
        self.status = status
        self.manager = manager
        self.uuid = generate_uuid()
        self.id = id or self.uuid
        self.items = items or {}
        self.deployment_uuid = deployment_uuid or generate_uuid()

    def __getattr__(self, name):
        # NOTE(msdubov): e.g. server.delete() -> manager.delete(server)
        def manager_func(*args, **kwargs):
            getattr(self.manager, name)(self, *args, **kwargs)
        return manager_func

    def __getitem__(self, key):
        return self.items[key]


class FakeServer(FakeResource):

    def suspend(self):
        self.status = "SUSPENDED"


class FakeFailedServer(FakeResource):

    def __init__(self, manager=None):
        super(FakeFailedServer, self).__init__(manager, status="ERROR")


class FakeImage(FakeResource):

    def __init__(self, manager=None, id="image-id-0", min_ram=0,
                 size=0, min_disk=0, name=None):
        super(FakeImage, self).__init__(manager, id=id, name=name)
        self.min_ram = min_ram
        self.size = size
        self.min_disk = min_disk
        self.update = mock.MagicMock()


class FakeFailedImage(FakeResource):

    def __init__(self, manager=None):
        super(FakeFailedImage, self).__init__(manager, status="error")


class FakeFloatingIP(FakeResource):
    pass


class FakeTenant(FakeResource):

    def __init__(self, manager, name):
        super(FakeTenant, self).__init__(manager, name=name)


class FakeUser(FakeResource):
    pass


class FakeNetwork(FakeResource):
    pass


class FakeFlavor(FakeResource):

    def __init__(self, id="flavor-id-0", manager=None, ram=0, disk=0):
        super(FakeFlavor, self).__init__(manager, id=id)
        self.ram = ram
        self.disk = disk


class FakeKeypair(FakeResource):
    pass


class FakeQuotas(FakeResource):
    pass


class FakeSecurityGroup(FakeResource):

    def __init__(self, manager=None, rule_manager=None):
        super(FakeSecurityGroup, self).__init__(manager)
        self.rule_manager = rule_manager

    @property
    def rules(self):
        return [rule for rule in self.rule_manager.list()
                if rule.parent_group_id == self.id]


class FakeSecurityGroupRule(FakeResource):
    def __init__(self, name, **kwargs):
        super(FakeSecurityGroupRule, self).__init__(name)
        if 'cidr' in kwargs:
            kwargs['ip_range'] = {'cidr': kwargs['cidr']}
            del kwargs['cidr']
        for key, value in kwargs.items():
            self.items[key] = value
            setattr(self, key, value)


class FakeVolume(FakeResource):
    pass


class FakeVolumeType(FakeResource):
    pass


class FakeVolumeTransfer(FakeResource):
    pass


class FakeVolumeSnapshot(FakeResource):
    pass


class FakeVolumeBackup(FakeResource):
    pass


class FakeRole(FakeResource):
    pass


class FakeManager(object):

    def __init__(self):
        super(FakeManager, self).__init__()
        self.cache = {}
        self.resources_order = []

    def get(self, resource_uuid):
        return self.cache.get(resource_uuid, None)

    def delete(self, resource_uuid):
        cached = self.get(resource_uuid)
        if cached is not None:
            cached.status = "DELETED"
            del self.cache[resource_uuid]
            self.resources_order.remove(resource_uuid)

    def _cache(self, resource):
        self.resources_order.append(resource.uuid)
        self.cache[resource.uuid] = resource
        return resource

    def list(self, **kwargs):
        return [self.cache[key] for key in self.resources_order]

    def find(self, **kwargs):
        for resource in self.cache.values():
            match = True
            for key, value in kwargs.items():
                if getattr(resource, key, None) != value:
                    match = False
                    break
            if match:
                return resource


class FakeServerManager(FakeManager):

    def __init__(self, image_mgr=None):
        super(FakeServerManager, self).__init__()
        self.images = image_mgr or FakeImageManager()

    def get(self, resource_uuid):
        server = self.cache.get(resource_uuid, None)
        if server is not None:
            return server
        raise exceptions.NotFound("Server %s not found" % (resource_uuid))

    def _create(self, server_class=FakeServer, name=None):
        server = self._cache(server_class(self))
        if name is not None:
            server.name = name
        return server

    def create(self, name, image_id, flavor_id, **kwargs):
        return self._create(name=name)

    def create_image(self, server, name):
        image = self.images._create()
        return image.uuid

    def add_floating_ip(self, server, fip):
        pass

    def remove_floating_ip(self, server, fip):
        pass


class FakeFailedServerManager(FakeServerManager):

    def create(self, name, image_id, flavor_id, **kwargs):
        return self._create(FakeFailedServer, name)


class FakeImageManager(FakeManager):

    def __init__(self):
        super(FakeImageManager, self).__init__()

    def get(self, resource_uuid):
        image = self.cache.get(resource_uuid, None)
        if image is not None:
            return image
        raise exc.HTTPNotFound("Image %s not found" % (resource_uuid))

    def _create(self, image_class=FakeImage, name=None):
        image = self._cache(image_class(self))
        if name is not None:
            image.name = name
        return image

    def create(self, name, copy_from, container_format, disk_format):
        return self._create(name=name)


class FakeFailedImageManager(FakeImageManager):

    def create(self, name, copy_from, container_format, disk_format):
        return self._create(FakeFailedImage, name)


class FakeFloatingIPsManager(FakeManager):

    def create(self):
        return FakeFloatingIP(self)


class FakeTenantsManager(FakeManager):

    def create(self, name):
        return self._cache(FakeTenant(self, name))


class FakeNetworkManager(FakeManager):

    def create(self, net_id):
        net = FakeNetwork(self)
        net.id = net_id
        return self._cache(net)


class FakeFlavorManager(FakeManager):

    def create(self):
        flv = FakeFlavor(self)
        return self._cache(flv)


class FakeKeypairManager(FakeManager):

    def create(self, name, public_key=None):
        kp = FakeKeypair(self)
        kp.name = name or kp.name
        return self._cache(kp)


class FakeNovaQuotasManager(FakeManager):

    def update(self, tenant_id, **kwargs):
        fq = FakeQuotas(self)
        return self._cache(fq)

    def delete(self, tenant_id):
        pass


class FakeSecurityGroupManager(FakeManager):
    def __init__(self, rule_manager=None):
        super(FakeSecurityGroupManager, self).__init__()
        self.rule_manager = rule_manager
        self.create('default')

    def create(self, name, description=""):
        sg = FakeSecurityGroup(
            manager=self,
            rule_manager=self.rule_manager)
        sg.name = name or sg.name
        sg.description = description
        return self._cache(sg)

    def find(self, name, **kwargs):
        kwargs['name'] = name
        for resource in self.cache.values():
            match = True
            for key, value in kwargs.items():
                if getattr(resource, key, None) != value:
                    match = False
                    break
            if match:
                return resource
        raise exceptions.NotFound('Security Group not found')


class FakeSecurityGroupRuleManager(FakeManager):
    def __init__(self):
        super(FakeSecurityGroupRuleManager, self).__init__()

    def create(self, parent_group_id, **kwargs):
        kwargs['parent_group_id'] = parent_group_id
        sgr = FakeSecurityGroupRule(self, **kwargs)
        return self._cache(sgr)


class FakeUsersManager(FakeManager):

    def create(self, username, password, email, tenant_id):
        return self._cache(FakeUser(self))


class FakeVolumeManager(FakeManager):

    def create(self, name=None):
        volume = FakeVolume(self)
        volume.name = name or volume.name
        return self._cache(volume)


class FakeVolumeTypeManager(FakeManager):

    def create(self, name):
        vol_type = FakeVolumeType(self)
        vol_type.name = name or vol_type.name
        return self._cache(vol_type)


class FakeVolumeTransferManager(FakeManager):

    def create(self, name):
        transfer = FakeVolumeTransfer(self)
        transfer.name = name or transfer.name
        return self._cache(transfer)


class FakeVolumeSnapshotManager(FakeManager):

    def create(self, name):
        snapshot = FakeVolumeSnapshot(self)
        snapshot.name = name or snapshot.name
        return self._cache(snapshot)


class FakeVolumeBackupManager(FakeManager):

    def create(self, name):
        backup = FakeVolumeBackup(self)
        backup.name = name or backup.name
        return self._cache(backup)


class FakeRolesManager(FakeManager):

    def create(self, role_id, name):
        role = FakeRole(self)
        role.name = name
        role.id = role_id
        return self._cache(role)

    def roles_for_user(self, user, tenant):
        role = FakeRole(self)
        role.name = 'admin'
        return [role, ]


class FakeServiceCatalog(object):
    def get_endpoints(self):
        return {'image': [{'publicURL': 'http://fake.to'}],
                'metering': [{'publicURL': 'http://fake.to'}]}


class FakeGlanceClient(object):

    def __init__(self, failed_image_manager=False):
        if failed_image_manager:
            self.images = FakeFailedImageManager()
        else:
            self.images = FakeImageManager()


class FakeCinderClient(object):

    def __init__(self):
        self.volumes = FakeVolumeManager()
        self.volume_types = FakeVolumeTypeManager()
        self.transfers = FakeVolumeTransferManager()
        self.volume_snapshots = FakeVolumeSnapshotManager()
        self.backups = FakeVolumeBackupManager()


class FakeNovaClient(object):

    def __init__(self, failed_server_manager=False):
        self.images = FakeImageManager()
        if failed_server_manager:
            self.servers = FakeFailedServerManager(self.images)
        else:
            self.servers = FakeServerManager(self.images)
        self.floating_ips = FakeFloatingIPsManager()
        self.networks = FakeNetworkManager()
        self.flavors = FakeFlavorManager()
        self.keypairs = FakeKeypairManager()
        self.security_group_rules = FakeSecurityGroupRuleManager()
        self.security_groups = FakeSecurityGroupManager(
            rule_manager=self.security_group_rules)
        self.quotas = FakeNovaQuotasManager()


class FakeKeystoneClient(object):

    def __init__(self):
        self.tenants = FakeTenantsManager()
        self.users = FakeUsersManager()
        self.roles = FakeRolesManager()
        self.project_id = 'abc123'
        self.auth_url = 'http://example.com:5000/v2.0/'
        self.auth_token = 'fake'
        self.auth_user_id = generate_uuid()
        self.auth_tenant_id = generate_uuid()
        self.service_catalog = FakeServiceCatalog()
        self.region_name = 'RegionOne'
        self.auth_ref = {'user': {'roles': [{'name': 'admin'}]}}

    def authenticate(self):
        return True


class FakeCeilometerClient(object):

    def __init__(self):
        #TODO(marcoemorais): Fake Manager subclasses to retrieve metrics.
        pass


class FakeNeutronClient(object):

    def __init__(self):
        #TODO(bsemp): Fake Manager subclasses to manage networks.
        pass


class FakeIronicClient(object):

    def __init__(self):
        # TODO(romcheg):Fake Manager subclasses to manage BM nodes.
        pass


class FakeClients(object):

    def __init__(self):
        self._nova = None
        self._glance = None
        self._keystone = None
        self._cinder = None
        self._endpoint = None

    def keystone(self):
        if self._keystone is not None:
            return self._keystone
        self._keystone = FakeKeystoneClient()
        return self._keystone

    def verified_keystone(self):
        return self.keystone()

    def nova(self):
        if self._nova is not None:
            return self._nova
        self._nova = FakeNovaClient()
        return self._nova

    def glance(self):
        if self._glance is not None:
            return self._glance
        self._glance = FakeGlanceClient()
        return self._glance

    def cinder(self):
        if self._cinder is not None:
            return self._cinder
        self._cinder = FakeCinderClient()
        return self._cinder


class FakeRunner(object):

    CONFIG_SCHEMA = {
        "type": "object",
        "$schema": rally_utils.JSON_SCHEMA,
        "properties": {
            "type": {
                "type": "string",
                "enum": ["fake"]
            },

            "a": {
                "type": "string"
            },

            "b": {
                "type": "number"
            }
        },
        "required": ["type", "a"]
    }


class FakeScenario(base.Scenario):

    def idle_time(self):
        return 0

    def do_it(self, **kwargs):
        pass

    def with_output(self, **kwargs):
        return {"data": {"a": 1}, "error": None}

    def too_long(self, **kwargs):
        pass

    def something_went_wrong(self, **kwargs):
        raise Exception("Something went wrong")

    def raise_timeout(self, **kwargs):
        raise multiprocessing.TimeoutError()


class FakeTimer(rally_utils.Timer):

    def duration(self):
        return 10


class FakeContext(base_ctx.Context):

    __ctx_name__ = "fake"

    CONFIG_SCHEMA = {
        "type": "object",
        "$schema": rally_utils.JSON_SCHEMA,
        "properties": {
            "test": {
                "type": "integer"
            },
        },
        "additionalProperties": False
    }

    def setup(self):
        pass

    def cleanup(self):
        pass


class FakeUserContext(FakeContext):

    admin = {
        "id": "adminuuid",
        "endpoint": endpoint.Endpoint("aurl", "aname", "apwd", "atenant")
    }
    user = {
        "id": "uuid",
        "endpoint": endpoint.Endpoint("url", "name", "pwd", "tenant")
    }
    tenant = {"id": "uuid", "nema": "tenant"}

    def __init__(self, context):
        context.setdefault("task", mock.MagicMock())
        super(FakeUserContext, self).__init__(context)

        context.setdefault("admin", FakeUserContext.admin)
        context.setdefault("users", [FakeUserContext.user])
        context.setdefault("tenants", [FakeUserContext.tenant])
        context.setdefault("scenario_name",
                           'NovaServers.boot_server_from_volume_and_delete')


class FakeDeployment(dict):
    update_status = mock.Mock()
