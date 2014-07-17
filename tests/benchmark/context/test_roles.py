# Copyright 2014: Mirantis Inc.
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

from rally.benchmark.context import roles
from tests import fakes
from tests import test


class RoleGeneratorTestCase(test.TestCase):

    def create_default_roles_and_patch_add_remove_fuinctions(self, fc):
        fc.keystone().roles.add_user_role = mock.MagicMock()
        fc.keystone().roles.remove_user_role = mock.MagicMock()

        self.assertEqual(0, len(fc.keystone().roles.list()))
        default_roles = [{"id": "r1", "name": "test_role1"},
                         {"id": "r2", "name": "test_role2"}]

        fc.keystone().roles.create(*default_roles[0].values())
        fc.keystone().roles.create(*default_roles[1].values())
        self.assertEqual(2, len(fc.keystone().roles.list()))

    @property
    def context(self):
        return {
            "config": {
                "roles": [
                    "test_role1",
                    "test_role2"
                ]
            },
            "admin": {"endpoint": mock.MagicMock()},
            "task": mock.MagicMock()
        }

    @mock.patch("rally.benchmark.context.roles.osclients")
    def test_add_role(self, mock_osclients):
        fc = fakes.FakeClients()
        mock_osclients.Clients.return_value = fc
        self.create_default_roles_and_patch_add_remove_fuinctions(fc)

        ctx = roles.RoleGenerator(self.context)
        ctx.context["users"] = [{"id": "u1", "tenant_id": "t1"},
                                {"id": "u2", "tenant_id": "t2"}]
        result = ctx._add_role(mock.MagicMock(),
                               self.context["config"]["roles"][0])

        expected = {"id": "r1", "name": "test_role1"}
        self.assertEqual(expected, result)

    @mock.patch("rally.benchmark.context.roles.osclients")
    def test_add_role_which_does_not_exist(self, mock_osclients):
        fc = fakes.FakeClients()
        mock_osclients.Clients.return_value = fc
        self.create_default_roles_and_patch_add_remove_fuinctions(fc)

        ctx = roles.RoleGenerator(self.context)
        ctx.context["users"] = [{"id": "u1", "tenant_id": "t1"},
                                {"id": "u2", "tenant_id": "t2"}]
        ex = self.assertRaises(Exception, ctx._add_role,
                               mock.MagicMock(), "unknown_role")

        expected = "Role 'unknown_role' does not exist in the list of roles"
        self.assertEqual(expected, str(ex))

    @mock.patch("rally.benchmark.context.roles.osclients")
    def test_remove_role(self, mock_osclients):
        role = mock.MagicMock()
        ctx = roles.RoleGenerator(self.context)
        ctx.context["users"] = [{"id": "u1", "tenant_id": "t1"},
                                {"id": "u2", "tenant_id": "t2"}]
        ctx._remove_role(mock.MagicMock(), role)
        calls = [
                mock.call("u1", role["id"], tenant="t1"),
                mock.call("u2", role["id"], tenant="t2"),
        ]
        mock_osclients.Clients().keystone()\
            .roles.remove_user_role.assert_has_calls(calls)

    @mock.patch("rally.benchmark.context.roles.osclients")
    def test_setup_and_cleanup(self, mock_osclients):
        fc = fakes.FakeClients()
        mock_osclients.Clients.return_value = fc
        self.create_default_roles_and_patch_add_remove_fuinctions(fc)

        with roles.RoleGenerator(self.context) as ctx:
            ctx.context["users"] = [{"id": "u1", "tenant_id": "t1"},
                                    {"id": "u2", "tenant_id": "t2"}]

            #self, user_id, role_id, tenant):
            ctx.setup()
            calls = [
                mock.call("u1", "r1", tenant="t1"),
                mock.call("u2", "r1", tenant="t2"),
                mock.call("u1", "r2", tenant="t1"),
                mock.call("u2", "r2", tenant="t2")
            ]
            fc.keystone().roles.add_user_role.assert_has_calls(calls)
            self.assertEqual(
                4, fc.keystone().roles.add_user_role.call_count)
            self.assertEqual(
                0, fc.keystone().roles.remove_user_role.call_count)
            self.assertEqual(2, len(ctx.context["roles"]))
            self.assertEqual(2, len(fc.keystone().roles.list()))

        # Cleanup (called by content manager)
        self.assertEqual(2, len(fc.keystone().roles.list()))
        self.assertEqual(4, fc.keystone().roles.add_user_role.call_count)
        self.assertEqual(4, fc.keystone().roles.remove_user_role.call_count)
        calls = [
            mock.call("u1", "r1", tenant="t1"),
            mock.call("u2", "r1", tenant="t2"),
            mock.call("u1", "r2", tenant="t1"),
            mock.call("u2", "r2", tenant="t2")
        ]
        fc.keystone().roles.remove_user_role.assert_has_calls(calls)
