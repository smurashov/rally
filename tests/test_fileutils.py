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
import os

from rally import fileutils
from tests import test


class FileUtilsTestCase(test.TestCase):

    @mock.patch('os.path.exists')
    @mock.patch.dict('os.environ', values={}, clear=True)
    def test_load_env_vile(self, mock_path):
        file_data = ["FAKE_ENV=fake_env\n"]
        mock_path.return_value = True
        with mock.patch('rally.fileutils.open', mock.mock_open(
                read_data=file_data), create=True) as mock_file:
            mock_file.return_value.readlines.return_value = file_data
            fileutils.load_env_file('path_to_file')
            self.assertIn('FAKE_ENV', os.environ)
            mock_file.return_value.readlines.assert_called_once_with()

    @mock.patch('os.path.exists')
    def test_update_env_file(self, mock_path):
        file_data = ["FAKE_ENV=old_value\n", "FAKE_ENV2=any\n"]
        mock_path.return_value = True
        with mock.patch('rally.fileutils.open', mock.mock_open(
                read_data=file_data), create=True) as mock_file:
            mock_file.return_value.readlines.return_value = file_data
            fileutils.update_env_file('path_to_file', 'FAKE_ENV', 'new_value')
            calls = [mock.call('FAKE_ENV2=any\n'), mock.call(
                'FAKE_ENV=new_value')]
            mock_file.return_value.readlines.assert_called_once_with()
            mock_file.return_value.write.assert_has_calls(calls)
