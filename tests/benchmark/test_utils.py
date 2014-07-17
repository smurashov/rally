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

import datetime
from tests import fakes
from tests import test

from rally.benchmark import utils
from rally import exceptions


class BenchmarkUtilsTestCase(test.TestCase):

    def test_chunks(self):
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

        self.assertEqual(utils.chunks(data, 3),
                         [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]])
        self.assertEqual(utils.chunks(data, 5),
                         [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10], [11, 12]])

    def test_resource_is(self):
        is_active = utils.resource_is("ACTIVE")
        self.assertTrue(is_active(fakes.FakeResource(status="active")))
        self.assertTrue(is_active(fakes.FakeResource(status="aCtIvE")))
        self.assertFalse(is_active(fakes.FakeResource(status="ERROR")))

    def test_infinite_run_args_generator(self):
        args = lambda x: (x, "a", "b", 123)
        for i, real_args in enumerate(utils.infinite_run_args_generator(args)):
            self.assertEqual((i, "a", "b", 123), real_args)
            if i > 5:
                break

    def test_manager_list_sizes(self):
        manager = fakes.FakeManager()

        def lst():
            return [1] * 10

        manager.list = lst
        manager_list_size = utils.manager_list_size([5])
        self.assertFalse(manager_list_size(manager))

        manager_list_size = utils.manager_list_size([10])
        self.assertTrue(manager_list_size(manager))

    def test_get_from_manager(self):
        get_from_manager = utils.get_from_manager()
        manager = fakes.FakeManager()
        resource = fakes.FakeResource(manager=manager)
        manager._cache(resource)
        self.assertEqual(get_from_manager(resource), resource)

    def test_get_from_manager_in_error_state(self):
        get_from_manager = utils.get_from_manager()
        manager = fakes.FakeManager()
        resource = fakes.FakeResource(manager=manager, status="ERROR")
        manager._cache(resource)
        self.assertRaises(exceptions.GetResourceFailure,
                          get_from_manager, resource)

    def test_get_from_manager_in_deleted_state(self):
        get_from_manager = utils.get_from_manager()
        manager = fakes.FakeManager()
        resource = fakes.FakeResource(manager=manager, status="DELETED")
        manager._cache(resource)
        self.assertRaises(exceptions.GetResourceNotFound,
                          get_from_manager, resource)

    def test_get_from_manager_not_found(self):
        get_from_manager = utils.get_from_manager()
        manager = mock.MagicMock()
        resource = fakes.FakeResource(manager=manager, status="ERROR")

        class NotFoundException(Exception):
            http_status = 404

        manager.get = mock.MagicMock(side_effect=NotFoundException)
        self.assertRaises(exceptions.GetResourceFailure,
                          get_from_manager, resource)

    def test_get_from_manager_http_exception(self):
        get_from_manager = utils.get_from_manager()
        manager = mock.MagicMock()
        resource = fakes.FakeResource(manager=manager, status="ERROR")

        class HTTPException(Exception):
            pass

        manager.get = mock.MagicMock(side_effect=HTTPException)
        self.assertRaises(exceptions.GetResourceFailure,
                          get_from_manager, resource)

    def test_run_concurrent_helper(self):
        cls = mock.MagicMock()
        args = (cls, "test", {})
        result = utils.run_concurrent_helper(args)
        self.assertEqual(cls.test(), result)


class WaitForTestCase(test.TestCase):

    def setUp(self):
        super(WaitForTestCase, self).setUp()
        self.resource = object()
        self.load_secs = 0.01
        self.fake_checker_delayed = self.get_fake_checker_delayed(
            seconds=self.load_secs)

    def get_fake_checker_delayed(self, **delay):
        deadline = datetime.datetime.now() + datetime.timedelta(**delay)
        return lambda obj: datetime.datetime.now() > deadline

    def fake_checker_false(self, obj):
        return False

    def fake_updater(self, obj):
        return obj

    def test_wait_for_with_updater(self):
        loaded_resource = utils.wait_for(self.resource,
                                         self.fake_checker_delayed,
                                         self.fake_updater,
                                         1, self.load_secs / 3)
        self.assertEqual(loaded_resource, self.resource)

    def test_wait_for_no_updater(self):
        loaded_resource = utils.wait_for(self.resource,
                                         self.fake_checker_delayed,
                                         None, 1, self.load_secs / 3)
        self.assertEqual(loaded_resource, self.resource)

    def test_wait_for_timeout_failure(self):
        self.assertRaises(exceptions.TimeoutException, utils.wait_for,
                          self.resource, self.fake_checker_false,
                          self.fake_updater, self.load_secs,
                          self.load_secs / 3)
