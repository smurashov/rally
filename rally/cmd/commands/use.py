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

""" Rally command: use """

import os

from rally.cmd import cliutils
from rally import db
from rally import exceptions
from rally import fileutils


class UseCommands(object):

    def _update_openrc_deployment_file(self, deploy_id, endpoints):
        openrc_path = os.path.expanduser('~/.rally/openrc-%s' % deploy_id)
        # NOTE(msdubov): In case of multiple endpoints write the first one.
        with open(openrc_path, 'w+') as env_file:
            if endpoints[0].get('region_name'):
                env_file.write('export OS_AUTH_URL=%(auth_url)s\n'
                               'export OS_USERNAME=%(username)s\n'
                               'export OS_PASSWORD=%(password)s\n'
                               'export OS_TENANT_NAME=%(tenant_name)s\n'
                               'export OS_REGION_NAME=%(region_name)s\n'
                               % endpoints[0])
            else:
                env_file.write('export OS_AUTH_URL=%(auth_url)s\n'
                               'export OS_USERNAME=%(username)s\n'
                               'export OS_PASSWORD=%(password)s\n'
                               'export OS_TENANT_NAME=%(tenant_name)s\n'
                               % endpoints[0])
        expanded_path = os.path.expanduser('~/.rally/openrc')
        if os.path.exists(expanded_path):
            os.remove(expanded_path)
        os.symlink(openrc_path, expanded_path)

    def _update_attribute_in_global_file(self, attribute, value):
        expanded_path = os.path.expanduser('~/.rally/globals')
        fileutils.update_env_file(expanded_path, attribute, '%s\n' % value)

    def _ensure_rally_configuration_dir_exists(self):
        if not os.path.exists(os.path.expanduser('~/.rally/')):
            os.makedirs(os.path.expanduser('~/.rally/'))

    @cliutils.args('--uuid', type=str, dest='deploy_id', required=False,
                   help='UUID of the deployment')
    @cliutils.args('--name', type=str, dest='name', required=False,
                   help='Name of the deployment')
    def deployment(self, deploy_id=None, name=None):
        """Set the RALLY_DEPLOYMENT env var to be used by all CLI commands

        :param deploy_id: a UUID of a deployment
        """
        if not (name or deploy_id):
            print('You should specify --name or --uuid of deployment')
            return 1

        deploy = None

        if name:
            deployments = db.deployment_list(name=name)
            if len(deployments) > 1:
                print("Multiple deployments found by name: `%s`" % name)
                return 1
            elif not deployments:
                print("There is no `%s` deployment" % name)
                return 1
            else:
                deploy = deployments[0]
                deploy_id = deploy["uuid"]

        try:
            deploy = deploy or db.deployment_get(deploy_id)
            print('Using deployment: %s' % deploy_id)
            self._ensure_rally_configuration_dir_exists()
            self._update_attribute_in_global_file('RALLY_DEPLOYMENT',
                                                  deploy_id)
            self._update_openrc_deployment_file(deploy_id,
                                                deploy['endpoints'])
            print ('~/.rally/openrc was updated\n\nHINTS:\n'
                   '* To get your cloud resources, run:\n\t'
                   'rally show [flavors|images|keypairs|networks|secgroups]\n'
                   '\n* To use standard OpenStack clients, set up your env by '
                   'running:\n\tsource ~/.rally/openrc\n'
                   '  OpenStack clients are now configured, e.g run:\n\t'
                   'glance image-list')
        except exceptions.DeploymentNotFound:
            print('Deployment %s is not found.' % deploy_id)
            return 1

    @cliutils.args('--uuid', type=str, dest='task_id', required=False,
                   help='UUID of the task')
    def task(self, task_id):
        """Set the RALLY_TASK env var so the user does not need to specify a
        task UUID in the command requiring this parameter.
        If the task uuid specified in parameter by the user does not exist,
        a TaskNotFound will be raised by task_get().

        :param task_id: a UUID of a task
        """
        print('Using task: %s' % task_id)
        self._ensure_rally_configuration_dir_exists()
        db.task_get(task_id)
        self._update_attribute_in_global_file('RALLY_TASK', task_id)
