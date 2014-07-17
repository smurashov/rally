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
import os

from rally.verification.verifiers.tempest import tempest
from tests import test


TEMPEST_PATH = 'rally.verification.verifiers.tempest'


class TempestTestCase(test.TestCase):

    def setUp(self):
        super(TempestTestCase, self).setUp()
        self.verifier = tempest.Tempest('fake_deploy_id',
                                        verification=mock.MagicMock())

        self.verifier.tempest_path = '/tmp'
        self.verifier.config_file = '/tmp/tempest.conf'
        self.verifier.log_file = '/tmp/tests_log.xml'
        self.regex = None

    @mock.patch('six.moves.builtins.open')
    def test__write_config(self, mock_open):
        conf = mock.Mock()
        mock_file = mock.MagicMock()
        mock_open.return_value = mock_file
        self.verifier._write_config(conf)
        mock_open.assert_called_once_with(self.verifier.config_file, 'w+')
        conf.write.assert_called_once_with(mock_file.__enter__())
        mock_file.__exit__.assert_called_once_with(None, None, None)

    @mock.patch('os.path.exists')
    def test_is_installed(self, mock_exists):
        mock_exists.return_value = True

        result = self.verifier.is_installed()

        mock_exists.assert_called_once_with(
            os.path.join(self.verifier.tempest_path, '.venv'))
        self.assertTrue(result)

    @mock.patch('rally.verification.verifiers.tempest.tempest.subprocess')
    def test__clone(self, mock_sp):
        self.verifier._clone()
        mock_sp.check_call.assert_called_once_with(
            ['git', 'clone', 'https://github.com/openstack/tempest',
             tempest.Tempest.tempest_base_path])

    @mock.patch(TEMPEST_PATH + '.tempest.Tempest._initialize_testr')
    @mock.patch(TEMPEST_PATH + '.tempest.Tempest._install_venv')
    @mock.patch(TEMPEST_PATH + '.tempest.subprocess')
    @mock.patch('os.path.exists')
    @mock.patch('shutil.copytree')
    def test_install(
            self, mock_copytree, mock_exists, mock_sp, mock_venv, mock_testr):
        mock_exists.side_effect = (False, True, False)
        # simulate tempest is clonned but is not installed for current deploy

        self.verifier.install()
        mock_copytree.assert_called_once_with(
            tempest.Tempest.tempest_base_path,
            self.verifier.tempest_path)
        mock_sp.check_call.assert_called_once_with(
            'git checkout master; git remote update; git pull',
            cwd=os.path.join(self.verifier.tempest_path, 'tempest'),
            shell=True)

    @mock.patch('rally.verification.verifiers.tempest.tempest.shutil')
    @mock.patch('os.path.exists')
    def test_uninstall(self, mock_exists, mock_shutil):
        mock_exists.return_value = True
        self.verifier.uninstall()
        mock_shutil.rmtree.assert_called_once_with(self.verifier.tempest_path)

    @mock.patch(TEMPEST_PATH + '.tempest.Tempest.env')
    @mock.patch(TEMPEST_PATH + '.tempest.subprocess')
    def test_run(self, mock_sp, mock_env):
        self.verifier.run('tempest.api.image')
        fake_call = (
            '%(venv)s testr run --parallel --subunit tempest.api.image '
            '| %(venv)s subunit2junitxml --forward '
            '--output-to=%(tempest_path)s/tests_log.xml '
            '| %(venv)s subunit-2to1 '
            '| %(venv)s %(tempest_path)s/tools/colorizer.py' % {
                'venv': self.verifier.venv_wrapper,
                'tempest_path': self.verifier.tempest_path})
        mock_sp.check_call.assert_called_once_with(
            fake_call, env=mock_env, cwd=self.verifier.tempest_path,
            shell=True)

    @mock.patch(TEMPEST_PATH + '.tempest.os.remove')
    @mock.patch(TEMPEST_PATH + '.tempest.Tempest.discover_tests')
    @mock.patch(TEMPEST_PATH + '.tempest.Tempest._initialize_testr')
    @mock.patch(TEMPEST_PATH + '.tempest.Tempest.run')
    @mock.patch(TEMPEST_PATH + '.tempest.Tempest._write_config')
    @mock.patch(TEMPEST_PATH + '.config.TempestConf')
    @mock.patch('rally.db.deployment_get')
    @mock.patch('rally.osclients.Clients')
    @mock.patch('rally.objects.endpoint.Endpoint')
    def test_verify(self, mock_endpoint, mock_osclients, mock_get, mock_conf,
                    mock_write, mock_run, mock_testr_init, mock_discover,
                    mock_os):
        fake_conf = mock.MagicMock()
        mock_conf().generate.return_value = fake_conf

        self.verifier.verify("smoke", None)
        mock_conf().generate.assert_called_once_with()
        mock_write.assert_called_once_with(fake_conf)
        mock_run.assert_called_once_with("smoke")

    @mock.patch('os.environ')
    def test__generate_env(self, mock_env):
        expected_env = {'PATH': '/some/path'}
        mock_env.copy.return_value = expected_env.copy()
        expected_env.update({
            'TEMPEST_CONFIG': 'tempest.conf',
            'TEMPEST_CONFIG_DIR': self.verifier.tempest_path,
            'OS_TEST_PATH': os.path.join(self.verifier.tempest_path,
                                         'tempest/test_discover')})
        self.assertIsNone(self.verifier._env)
        self.verifier._generate_env()
        self.assertEqual(expected_env, self.verifier._env)

    @mock.patch('os.path.isdir')
    @mock.patch(TEMPEST_PATH + '.tempest.subprocess')
    def test__venv_install_when_venv_exists(self, mock_sp, mock_isdir):
        mock_isdir.return_value = True
        self.verifier._install_venv()

        mock_isdir.assert_called_once_with(
            os.path.join(self.verifier.tempest_path, '.venv'))
        self.assertFalse(mock_sp.called)

    @mock.patch('os.path.isdir')
    @mock.patch(TEMPEST_PATH + '.tempest.subprocess.check_call')
    def test__venv_install_when_venv_not_exist(self, mock_sp, mock_isdir):
        mock_isdir.return_value = False
        self.verifier._install_venv()

        mock_isdir.assert_called_once_with(
            os.path.join(self.verifier.tempest_path, '.venv'))
        mock_sp.assert_has_calls([
            mock.call('python ./tools/install_venv.py', shell=True,
                      cwd=self.verifier.tempest_path),
            mock.call('%s pip install junitxml' % self.verifier.venv_wrapper,
                      shell=True, cwd=self.verifier.tempest_path),
            mock.call('%s python setup.py install' %
                      self.verifier.venv_wrapper, shell=True,
                      cwd=self.verifier.tempest_path)])

    @mock.patch('os.path.isdir')
    @mock.patch(TEMPEST_PATH + '.tempest.subprocess')
    def test__initialize_testr_when_testr_already_initialized(
            self, mock_sp, mock_isdir):
        mock_isdir.return_value = True
        self.verifier._initialize_testr()

        mock_isdir.assert_called_once_with(
            os.path.join(self.verifier.tempest_path, '.testrepository'))
        self.assertFalse(mock_sp.called)

    @mock.patch('os.path.isdir')
    @mock.patch(TEMPEST_PATH + '.tempest.subprocess.check_call')
    def test__initialize_testr_when_testr_not_initialized(
            self, mock_sp, mock_isdir):
        mock_isdir.return_value = False
        self.verifier._initialize_testr()

        mock_isdir.assert_called_once_with(
            os.path.join(self.verifier.tempest_path, '.testrepository'))
        mock_sp.assert_called_once_with(
            '%s testr init' % self.verifier.venv_wrapper, shell=True,
            cwd=self.verifier.tempest_path)

    @mock.patch('xml.dom.minidom.parse')
    @mock.patch('os.path.isfile')
    def test__save_results_without_log_file(self, mock_isfile, mock_parse):
        mock_isfile.return_value = False

        self.verifier._save_results()

        mock_isfile.assert_called_once_with(self.verifier.log_file)
        self.assertEqual(0, mock_parse.call_count)

    @mock.patch('os.path.isfile')
    def test__save_results_with_log_file(self, mock_isfile):
        mock_isfile.return_value = True
        self.verifier.log_file = os.path.join(os.path.dirname(__file__),
                                              'fake_log.xml')
        self.verifier._save_results()
        mock_isfile.assert_called_once_with(self.verifier.log_file)
        self.assertEqual(
            1, self.verifier.verification.finish_verification.call_count)
