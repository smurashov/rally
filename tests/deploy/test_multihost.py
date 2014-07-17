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
import uuid

from rally import consts
from rally import deploy
from tests import fakes
from tests import test

MOD = 'rally.deploy.engines.multihost.'


class TestMultihostEngine(test.TestCase):
    def setUp(self):
        super(TestMultihostEngine, self).setUp()
        self.config = {
            "type": "MultihostEngine",
            "controller": {
                "type": "DummyEngine",
                "endpoint": {'auth_url': 'http://h1.net'}
            },
            "nodes": [
                {
                    "type": "DummyEngine",
                    "endpoint": {'auth_url': 'endpoint1'},
                },
                {
                    "type": "DummyEngine",
                    "endpoint": {'auth_url': 'endpoint2',
                                 'cnt': '{controller_ip}'}
                }
            ]
        }
        self.deployment = fakes.FakeDeployment(
            uuid=str(uuid.uuid4()),
            config=self.config,
        )
        self.engine = deploy.engine.EngineFactory.get_engine('MultihostEngine',
                                                             self.deployment)

    @mock.patch(MOD + 'objects.Deployment')
    @mock.patch(MOD + 'engine.EngineFactory')
    def test__deploy_node(self, fakeEngineFactory, fakeDeployment):
        fake_endpoint = mock.Mock()
        fake_deployment = mock.Mock()
        fake_engine = mock.Mock()
        fake_engine.__enter__ = mock.Mock()
        fake_engine.__exit__ = mock.Mock()
        fake_engine.make_deploy = mock.Mock(return_value=fake_endpoint)

        fakeDeployment.return_value = fake_deployment
        fakeEngineFactory.get_engine = mock.Mock(return_value=fake_engine)

        engine, endpoint = self.engine._deploy_node(self.config['nodes'][0])

        self.assertEqual(fake_engine, engine)
        self.assertEqual(fake_endpoint, endpoint)

        fakeDeployment.assert_called_once_with(
            config=self.config['nodes'][0],
            parent_uuid=self.deployment['uuid'])
        fake_engine.__enter__.assert_called_once_with()
        fake_engine.__exit__.assert_called_once_with(None, None, None)

    def test__update_controller_ip(self):
        self.engine.controller_ip = '1.2.3.4'
        self.engine._update_controller_ip(self.config)
        expected = {'auth_url': 'endpoint2', 'cnt': '1.2.3.4'}
        self.assertEqual(expected, self.config['nodes'][1]['endpoint'])

    @mock.patch(MOD + 'MultihostEngine._deploy_node')
    @mock.patch(MOD + 'MultihostEngine._update_controller_ip')
    def test_deploy(self, update_ip, deploy_node):
        fake_endpoints = [mock.Mock()]
        fake_endpoints[0].auth_url = 'http://h1.net'
        deploy_node.return_value = [mock.Mock(), fake_endpoints]

        endpoints = self.engine.deploy()

        self.assertEqual(self.engine.controller_ip, 'h1.net')
        self.assertEqual(fake_endpoints, endpoints)
        expected = [
            mock.call(self.config['nodes'][0]),
            mock.call(self.config['nodes'][1]),
        ]
        self.assertEqual(expected, update_ip.mock_calls)
        self.deployment.update_status.assert_called_once_with(
            consts._DeployStatus.DEPLOY_SUBDEPLOY)

    @mock.patch(MOD + 'orchestrator')
    @mock.patch(MOD + 'db')
    def test_cleanup(self, m_db, m_orc):
        m_db.deployment_list.return_value = [{'uuid': 'uuid1'},
                                             {'uuid': 'uuid2'}]
        self.engine.cleanup()
        api_calls = [
            mock.call.api.destroy_deploy('uuid1'),
            mock.call.api.destroy_deploy('uuid2'),
        ]
        self.assertEqual(api_calls, m_orc.mock_calls)
