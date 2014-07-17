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

"""Test for Rally utils."""

from __future__ import print_function

import mock
import sys
import time

from rally import exceptions
from rally.openstack.common.gettextutils import _
from rally import utils
from tests import test


class ImmutableMixinTestCase(test.TestCase):

    def test_without_base_values(self):
        im = utils.ImmutableMixin()
        self.assertRaises(exceptions.ImmutableException,
                          im.__setattr__, 'test', 'test')

    def test_with_base_values(self):

        class A(utils.ImmutableMixin):
            def __init__(self, test):
                self.test = test
                super(A, self).__init__()

        a = A('test')
        self.assertRaises(exceptions.ImmutableException,
                          a.__setattr__, 'abc', 'test')
        self.assertEqual(a.test, 'test')


class EnumMixinTestCase(test.TestCase):

    def test_enum_mix_in(self):

        class Foo(utils.EnumMixin):
            a = 10
            b = 20
            CC = "2000"

        self.assertEqual(set(list(Foo())), set([10, 20, "2000"]))


class StdIOCaptureTestCase(test.TestCase):

    def test_stdout_capture(self):
        stdout = sys.stdout
        messages = ['abcdef', 'defgaga']
        with utils.StdOutCapture() as out:
            for msg in messages:
                print(msg)

        self.assertEqual(out.getvalue().rstrip('\n').split('\n'), messages)
        self.assertEqual(stdout, sys.stdout)

    def test_stderr_capture(self):
        stderr = sys.stderr
        messages = ['abcdef', 'defgaga']
        with utils.StdErrCapture() as err:
            for msg in messages:
                print(msg, file=sys.stderr)

        self.assertEqual(err.getvalue().rstrip('\n').split('\n'), messages)
        self.assertEqual(stderr, sys.stderr)


class TimerTestCase(test.TestCase):

    def test_timer_duration(self):
        start_time = time.time()
        end_time = time.time()

        with mock.patch('rally.utils.time') as mock_time:
            mock_time.time = mock.MagicMock(return_value=start_time)
            with utils.Timer() as timer:
                mock_time.time = mock.MagicMock(return_value=end_time)

        self.assertIsNone(timer.error)
        self.assertEqual(end_time - start_time, timer.duration())

    def test_timer_exception(self):
        try:
            with utils.Timer() as timer:
                raise Exception()
        except Exception:
            pass
        self.assertEqual(3, len(timer.error))
        self.assertEqual(timer.error[0], type(Exception()))


class IterSubclassesTestCase(test.TestCase):

    def test_itersubclasses(self):
        class A(object):
            pass

        class B(A):
            pass

        class C(A):
            pass

        class D(C):
            pass

        self.assertEqual([B, C, D], list(utils.itersubclasses(A)))


class ImportModulesTestCase(test.TestCase):
    def test_try_append_module_into_sys_modules(self):
        modules = {}
        utils.try_append_module('rally.version', modules)
        self.assertTrue('rally.version' in modules)

    def test_try_append_broken_module(self):
        modules = {}
        self.assertRaises(ImportError,
                          utils.try_append_module,
                          'tests.fixtures.import.broken',
                          modules)

    def test_import_modules_from_package(self):
        utils.import_modules_from_package('tests.fixtures.import.package')
        self.assertTrue('tests.fixtures.import.package.a' in sys.modules)
        self.assertTrue('tests.fixtures.import.package.b' in sys.modules)


class LogTestCase(test.TestCase):

    def test_log_task_wrapper(self):
        mock_log = mock.MagicMock()
        msg = "test %(a)s %(b)s"

        class TaskLog(object):

            def __init__(self):
                self.task = {'uuid': 'some_uuid'}

            @utils.log_task_wrapper(mock_log, msg, a=10, b=20)
            def some_method(self, x, y):
                return x + y

        t = TaskLog()
        self.assertEqual(t.some_method.__name__, "some_method")
        self.assertEqual(t.some_method(2, 2), 4)
        params = {'msg': msg % {'a': 10, 'b': 20}, 'uuid': t.task['uuid']}
        expected = [
            mock.call(_("Task %(uuid)s | Starting:  %(msg)s") % params),
            mock.call(_("Task %(uuid)s | Completed: %(msg)s") % params)
        ]
        self.assertEqual(mock_log.mock_calls, expected)


class LoadExtraModulesTestCase(test.TestCase):

    @mock.patch("rally.utils.imp.load_module")
    @mock.patch("rally.utils.imp.find_module")
    @mock.patch("rally.utils.os.path.exists")
    @mock.patch("rally.utils.os.path.isfile")
    @mock.patch("rally.utils.os.listdir")
    def test_load_plugins_successfull(self, mock_listdir, mock_isfile,
                                      mock_exists, mock_find_module,
                                      mock_load_module):
        mock_listdir.return_value = ["plugin1.py", "plugin2.py",
                                     "somethingnotpythonmodule",
                                     "somestrangedir.py"]
        mock_exists.return_value = True

        # check we don't try to load something that is not file
        def isfile_side_effect(*args):
            return args[0] != "/somewhere/somestrangedir.py"
        mock_isfile.side_effect = isfile_side_effect

        mock_find_module.return_value = (mock.MagicMock(), None, None)
        test_path = "/somewhere"
        utils.load_plugins(test_path)
        expected = [
            mock.call("plugin1", ["/somewhere"]),
            mock.call("plugin2", ["/somewhere"])
        ]
        self.assertEqual(mock_find_module.mock_calls, expected)
        self.assertEqual(len(mock_load_module.mock_calls), 2)

    @mock.patch("rally.utils.os")
    def test_load_plugins_from_nonexisting_and_empty_dir(self, mock_os):
        # test no fails for nonexisting directory
        mock_os.path.exists.return_value = False
        utils.load_plugins("/somewhere")
        # test no fails for empty directory
        mock_os.path.exists.return_value = True
        mock_os.listdir.return_value = []
        utils.load_plugins("/somewhere")

    @mock.patch("rally.utils.imp.load_module")
    @mock.patch("rally.utils.imp.find_module")
    @mock.patch("rally.utils.os.path")
    @mock.patch("rally.utils.os.listdir")
    def test_load_plugins_fails(self, mock_oslistdir, mock_ospath,
                                mock_load_module, mock_find_module):
        mock_ospath.exists.return_value = True
        mock_oslistdir.return_value = ["somebrokenplugin.py", ]
        mock_load_module.side_effect = Exception()
        # test no fails if module is broken
        # TODO(olkonami): check exception is handled correct
        utils.load_plugins("/somwhere")
