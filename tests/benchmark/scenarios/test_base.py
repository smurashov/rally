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
import traceback

from rally.benchmark.context import base as base_ctx
from rally.benchmark.scenarios import base
from rally.benchmark import validation
from rally import consts
from rally import exceptions
from tests import fakes
from tests import test


class ScenarioTestCase(test.TestCase):

    def test_get_by_name(self):

        class Scenario1(base.Scenario):
            pass

        class Scenario2(base.Scenario):
            pass

        for s in [Scenario1, Scenario2]:
            self.assertEqual(s, base.Scenario.get_by_name(s.__name__))

    def test_get_by_name_not_found(self):
        self.assertRaises(exceptions.NoSuchScenario,
                          base.Scenario.get_by_name, "non existing scenario")

    def test__validate_helper(self):
        validators = [
            mock.MagicMock(return_value=validation.ValidationResult()),
            mock.MagicMock(return_value=validation.ValidationResult())
        ]
        clients = mock.MagicMock()
        args = {"a": 1, "b": 2}
        task = mock.MagicMock()
        base.Scenario._validate_helper(validators, clients, args, task)
        for validator in validators:
            validator.assert_called_with(clients=clients, task=task, **args)

    def test__validate_helper__no_valid(self):
        validators = [
            mock.MagicMock(return_value=validation.ValidationResult()),
            mock.MagicMock(
                return_value=validation.ValidationResult(is_valid=False)
            )
        ]
        clients = mock.MagicMock()
        args = {"a": 1, "b": 2}
        self.assertRaises(exceptions.InvalidScenarioArgument,
                          base.Scenario._validate_helper,
                          validators, clients, args, 'fake_uuid')

    @mock.patch("rally.benchmark.scenarios.base.Scenario.get_by_name")
    def test_validate__no_validators(self, mock_base_get_by_name):

        class FakeScenario(fakes.FakeScenario):
            pass

        FakeScenario.do_it = mock.MagicMock()
        FakeScenario.do_it.validators = []
        mock_base_get_by_name.return_value = FakeScenario

        base.Scenario.validate("FakeScenario.do_it", {"a": 1, "b": 2})

        mock_base_get_by_name.assert_called_once_with("FakeScenario")

    @mock.patch("rally.benchmark.scenarios.base.Scenario._validate_helper")
    @mock.patch("rally.benchmark.scenarios.base.Scenario.get_by_name")
    def test_validate__admin_validators(self, mock_base_get_by_name,
                                        mock_validate_helper):

        class FakeScenario(fakes.FakeScenario):
            pass

        FakeScenario.do_it = mock.MagicMock()
        mock_base_get_by_name.return_value = FakeScenario

        validators = [mock.MagicMock(), mock.MagicMock()]
        for validator in validators:
            validator.permission = consts.EndpointPermission.ADMIN

        FakeScenario.do_it.validators = validators
        task = mock.MagicMock()
        args = {"a": 1, "b": 2}
        base.Scenario.validate("FakeScenario.do_it", args, admin="admin",
                               task=task)
        mock_validate_helper.assert_called_once_with(validators, "admin", args,
                                                     task)

    @mock.patch("rally.benchmark.scenarios.base.Scenario._validate_helper")
    @mock.patch("rally.benchmark.scenarios.base.Scenario.get_by_name")
    def test_validate_user_validators(self, mock_base_get_by_name,
                                      mock_validate_helper):

        class FakeScenario(fakes.FakeScenario):
            pass

        FakeScenario.do_it = mock.MagicMock()
        mock_base_get_by_name.return_value = FakeScenario

        validators = [mock.MagicMock(), mock.MagicMock()]
        for validator in validators:
            validator.permission = consts.EndpointPermission.USER

        FakeScenario.do_it.validators = validators
        args = {"a": 1, "b": 2}
        base.Scenario.validate("FakeScenario.do_it", args, users=["u1", "u2"])

        mock_validate_helper.assert_has_calls([
            mock.call(validators, "u1", args, None),
            mock.call(validators, "u2", args, None)
        ])

    def test_meta_string_returns_non_empty_list(self):

        class MyFakeScenario(fakes.FakeScenario):
            pass

        attr_name = 'preprocessors'
        preprocessors = [mock.MagicMock(), mock.MagicMock()]
        MyFakeScenario.do_it.__dict__[attr_name] = preprocessors

        scenario = MyFakeScenario()
        self.assertEqual(scenario.meta(cls="MyFakeScenario.do_it",
                                       attr_name=attr_name), preprocessors)

    def test_meta_class_returns_non_empty_list(self):

        class MyFakeScenario(fakes.FakeScenario):
            pass

        attr_name = 'preprocessors'
        preprocessors = [mock.MagicMock(), mock.MagicMock()]
        MyFakeScenario.do_it.__dict__[attr_name] = preprocessors

        scenario = MyFakeScenario()
        self.assertEqual(scenario.meta(cls=MyFakeScenario, method_name="do_it",
                                       attr_name=attr_name), preprocessors)

    def test_meta_string_returns_empty_list(self):

        class MyFakeScenario(fakes.FakeScenario):
            pass

        empty_list = []
        scenario = MyFakeScenario()
        self.assertEqual(scenario.meta(cls="MyFakeScenario.do_it",
                                       attr_name="foo", default=empty_list),
                         empty_list)

    def test_meta_class_returns_empty_list(self):

        class MyFakeScenario(fakes.FakeScenario):
            pass

        empty_list = []
        scenario = MyFakeScenario()
        self.assertEqual(scenario.meta(cls=MyFakeScenario, method_name="do_it",
                                       attr_name="foo", default=empty_list),
                         empty_list)

    def test_sleep_between_invalid_args(self):
        scenario = base.Scenario()
        self.assertRaises(exceptions.InvalidArgumentsException,
                          scenario.sleep_between, 15, 5)

        self.assertRaises(exceptions.InvalidArgumentsException,
                          scenario.sleep_between, -1, 0)

        self.assertRaises(exceptions.InvalidArgumentsException,
                          scenario.sleep_between, 0, -2)

    def test_sleep_between(self):
        scenario = base.Scenario()
        scenario.sleep_between(0.001, 0.002)
        self.assertTrue(0.001 <= scenario.idle_duration() <= 0.002)

    def test_sleep_beetween_multi(self):
        scenario = base.Scenario()
        scenario.sleep_between(0.001, 0.001)
        scenario.sleep_between(0.004, 0.004)
        self.assertEqual(scenario.idle_duration(), 0.005)

    @mock.patch("rally.benchmark.scenarios.base.time.sleep")
    @mock.patch("rally.benchmark.scenarios.base.random.uniform")
    def test_sleep_between_internal(self, mock_uniform, mock_sleep):
        scenario = base.Scenario()

        mock_uniform.return_value = 1.5
        scenario.sleep_between(1, 2)

        mock_sleep.assert_called_once_with(mock_uniform.return_value)
        self.assertEqual(scenario.idle_duration(), mock_uniform.return_value)

    def test_context(self):
        context = mock.MagicMock()
        scenario = base.Scenario(context=context)
        self.assertEqual(context, scenario.context())

    def test_clients(self):
        clients = fakes.FakeClients()

        scenario = base.Scenario(clients=clients)
        self.assertEqual(clients.nova(), scenario.clients("nova"))
        self.assertEqual(clients.glance(), scenario.clients("glance"))

    def test_admin_clients(self):
        clients = fakes.FakeClients()

        scenario = base.Scenario(admin_clients=clients)
        self.assertEqual(clients.nova(), scenario.admin_clients("nova"))
        self.assertEqual(clients.glance(), scenario.admin_clients("glance"))

    def test_scenario_context_are_valid(self):
        scenarios = base.Scenario.list_benchmark_scenarios()

        for scenario in scenarios:
            cls_name, method_name = scenario.split(".", 1)
            cls = base.Scenario.get_by_name(cls_name)
            context = getattr(cls, method_name).context
            try:
                base_ctx.ContextManager.validate(context)
            except Exception:
                print(traceback.format_exc())
                self.assertTrue(False,
                                "Scenario `%s` has wrong context" % scenario)

    def test_RESOURCE_NAME_PREFIX(self):
        self.assertTrue(isinstance(base.Scenario.RESOURCE_NAME_PREFIX,
                                   basestring))

    def test_RESOURCE_NAME_LENGTH(self):
        self.assertTrue(isinstance(base.Scenario.RESOURCE_NAME_LENGTH, int))
        self.assertTrue(base.Scenario.RESOURCE_NAME_LENGTH > 4)

    @mock.patch(
        "rally.benchmark.scenarios.base.Scenario.RESOURCE_NAME_PREFIX",
        "prefix_")
    def test_generate_random_name(self):
        set_by_length = lambda lst: set(map(len, lst))
        len_by_prefix = lambda lst, prefix:\
            len(filter(bool, map(lambda i: i.startswith(prefix), lst)))
        range_num = 50

        # Defaults
        result = [base.Scenario._generate_random_name()
                  for i in range(range_num)]
        self.assertEqual(len(result), len(set(result)))
        self.assertEqual(
            set_by_length(result),
            set([(len(
                base.Scenario.RESOURCE_NAME_PREFIX) +
                base.Scenario.RESOURCE_NAME_LENGTH)]))
        self.assertEqual(
            len_by_prefix(result, base.Scenario.RESOURCE_NAME_PREFIX),
            range_num)

        # Custom prefix
        prefix = "another_prefix_"
        result = [base.Scenario._generate_random_name(prefix)
                  for i in range(range_num)]
        self.assertEqual(len(result), len(set(result)))
        self.assertEqual(
            set_by_length(result),
            set([len(prefix) + base.Scenario.RESOURCE_NAME_LENGTH]))
        self.assertEqual(
            len_by_prefix(result, prefix), range_num)

        # Custom length
        name_length = 12
        result = [base.Scenario._generate_random_name(length=name_length)
                  for i in range(range_num)]
        self.assertEqual(len(result), len(set(result)))
        self.assertEqual(
            set_by_length(result),
            set([len(base.Scenario.RESOURCE_NAME_PREFIX) + name_length]))
        self.assertEqual(
            len_by_prefix(result, base.Scenario.RESOURCE_NAME_PREFIX),
            range_num)
