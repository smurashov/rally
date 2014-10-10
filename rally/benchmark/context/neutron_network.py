# Copyright 2014: Mirantis Inc
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

import six

from rally.benchmark.context import base
from rally.openstack.common.gettextutils import _
from rally.openstack.common import log as logging
from rally import osclients
from rally import utils

LOG = logging.getLogger(__name__)


class NeutronNetwork(base.Context):
    __ctx_name__ = "neutron_network"
    __ctx_order__ = 400
    __ctx_hidden__ = False

    PATTERN_ROUTER = "ctx_rally_%(tenant)s_router"
    PATTERN_NETWORK = "ctx_rally_%(tenant)s_network"

    CONFIG_SCHEMA = {
        "type": "object",
        "$schema": utils.JSON_SCHEMA,
        "properties": {
            "network_ip_version": {
                "type": "integer"
            },
            "network_cidr": {
                "type": "string"
            },
        },
        "additionalProperties": False
    }

    def __init__(self, context):
        super(NeutronNetwork, self).__init__(context)
        self.config.setdefault("network_ip_version", 4)
        self.config.setdefault("network_cidr", "10.%s.0.0/24")

    @classmethod
    def _network_remove(cls, neutron, tenant_id):
        router_name = cls.PATTERN_ROUTER % {"tenant": tenant_id}

        # Get dictionaries of elements.
        router = neutron.list_routers(name=router_name)["routers"][0]

        neutron.remove_gateway_router(router["id"])
        neutron.delete_router(router["id"])

    @classmethod
    def _generate_network(cls, neutron, args):
        tenant_id, network_ip_version, network_cidr = args
        router_name = cls.PATTERN_ROUTER % {"tenant": tenant_id}

        # Find the external network.
        for network in neutron.list_networks()["networks"]:
            if network.get("router:external"):
                external_network = network

        # Create router and add external network to this router.
        gw_info = {"network_id": external_network["id"],
                   "enable_snat": True}
        router_info = {"router": {"name": router_name,
                                  "external_gateway_info": gw_info,
                                  "tenant_id": tenant_id}}
        neutron.create_router(router_info)

    @utils.log_task_wrapper(LOG.info, _("Enter context: `neutron_network`"))
    def setup(self):
        admin_endpoint = self.context["admin"]["endpoint"]

        for index, tenant in enumerate(self.context["tenants"]):
            # Generate CIDR for new network
            args = (tenant["id"],
                    self.config["network_ip_version"],
                    self.config["network_cidr"] % index)

            neutron_client = osclients.Clients(admin_endpoint).neutron()
            self._generate_network(neutron_client, args)

    @utils.log_task_wrapper(LOG.info, _("Exit context: `neutron_network`"))
    def cleanup(self):
        admin_endpoint = self.context["admin"]["endpoint"]
        neutron_client = osclients.Clients(admin_endpoint).neutron()
        for tenant in self.context["tenants"]:
            try:
                self._network_remove(neutron_client, tenant["id"])
            except Exception as e:
                LOG.warning(_("Unable to delete network for tenant "
                              "%(tenant)s: %(message)s")
                            % {'tenant': tenant["name"],
                               'message': six.text_type(e)})
