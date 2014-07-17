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

import mock

from rally.benchmark.context import neutron_network
from tests import test


class NeutronNetworkContextTestCase(test.TestCase):

    router_id = 1
    network_id = 707
    subnet_id = 100
    external_network_id = 2000

    def setUp(self):
        super(NeutronNetworkContextTestCase, self).setUp()

        lr = {"routers": [{"name": "test_router", "id": self.router_id}, ]}
        ln = {"networks": [{"name": "test_network", "id": self.network_id},
                           {"name": "ext_net", "router:external": True,
                            "id": self.external_network_id}]}
        lsn = {"subnets": [{"name": "test_subnet", "id": self.subnet_id}, ]}

        self.neutron = neutron_network.NeutronNetwork
        self.nclient = mock.MagicMock()
        self.nclient.list_routers = mock.MagicMock(return_value=lr)
        self.nclient.list_networks = mock.MagicMock(return_value=ln)
        self.nclient.list_subnets = mock.MagicMock(return_value=lsn)

    def test_remove_network(self):
        self.neutron._network_remove(self.nclient, 1)

        self.nclient.remove_gateway_router.assert_called_with(self.router_id)
        self.nclient.remove_interface_router.assert_called_with(
            self.router_id, {"subnet_id": self.subnet_id})
        self.nclient.delete_router.assert_called_with(self.router_id)
        self.nclient.delete_network.assert_called_with(self.network_id)
        self.nclient.delete_subnet.assert_called_with(self.subnet_id)

    def test_generate_network(self):
        tenant_id = "4534343"
        router_name = self.neutron.PATTERN_ROUTER % {"tenant": tenant_id}
        network_name = self.neutron.PATTERN_NETWORK % {"tenant": tenant_id}
        args = (tenant_id, 4, "192.168.1.0/24")

        self.neutron._generate_network(self.nclient, args)

        gw_info = {"network_id": self.external_network_id,
                   "enable_snat": True}
        router_parameters = {"router": {"name": router_name,
                                        "external_gateway_info": gw_info,
                                        "tenant_id": tenant_id}}
        net_parameters = {"network": {"name": network_name,
                                      "tenant_id": tenant_id}}
        subnet_parameters = {"subnet": {"network_id": self.network_id,
                                        "ip_version": args[1],
                                        "cidr": args[2],
                                        "tenant_id": tenant_id}}

        self.nclient.list_networks.assert_called()
        self.nclient.create_router.assert_called_with(router_parameters)
        self.nclient.create_network.assert_called_with(net_parameters)
        self.nclient.create_subnet.assert_called_with(subnet_parameters)
