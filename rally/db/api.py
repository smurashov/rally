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

"""Defines interface for DB access.

The underlying driver is loaded as a :class:`LazyPluggable`.

Functions in this module are imported into the rally.db namespace. Call these
functions from rally.db namespace, not the rally.db.api namespace.

All functions in this module return objects that implement a dictionary-like
interface. Currently, many of these objects are sqlalchemy objects that
implement a dictionary interface. However, a future goal is to have all of
these objects be simple dictionaries.


**Related Flags**

:backend:  string to lookup in the list of LazyPluggable backends.
           `sqlalchemy` is the only supported backend right now.

:connection:  string specifying the sqlalchemy connection to use, like:
              `sqlite:///var/lib/cinder/cinder.sqlite`.

:enable_new_services:  when adding a new service to the database, is it in the
                       pool of available hardware (Default: True)

"""

from oslo.config import cfg

from rally.openstack.common.db import api as db_api


CONF = cfg.CONF


CONF.import_opt('backend', 'rally.openstack.common.db.options',
                group='database')


_BACKEND_MAPPING = {'sqlalchemy': 'rally.db.sqlalchemy.api'}

IMPL = db_api.DBAPI(CONF.database.backend, backend_mapping=_BACKEND_MAPPING)


def db_cleanup():
    """Recreate engine."""
    IMPL.db_cleanup()


def db_create():
    """Initialize DB. This method will drop existing database."""
    IMPL.db_create()


def db_drop():
    """Drop DB. This method drop existing database."""
    IMPL.db_drop()


def task_get(uuid):
    """Returns task by uuid.

    :param uuid: UUID of the task.
    :raises: :class:`rally.exceptions.TaskNotFound` if the task does not exist.
    :returns: task dict with data on the task.
    """
    return IMPL.task_get(uuid)


def task_get_detailed_last():
    """Returns the most recently created task."""
    return IMPL.task_get_detailed_last()


def task_get_detailed(uuid):
    """Returns task with results by uuid.

    :param uuid: UUID of the task.
    :returns: task dict with data on the task and its results.
    """
    return IMPL.task_get_detailed(uuid)


def task_create(values):
    """Create task record in DB.

    :param values: dict with record values.
    :returns: task dict with data on the task.
    """
    return IMPL.task_create(values)


def task_update(uuid, values):
    """Update task by values.

    :param uuid: UUID of the task.
    :param values: dict with record values.
    :raises: :class:`rally.exceptions.TaskNotFound` if the task does not exist.
    :returns: new updated task dict with data on the task.
    """
    return IMPL.task_update(uuid, values)


def task_list(status=None):
    """Get a list of tasks.

    :param status: Task status to filter the returned list on. If set to
                   None, all the tasks will be returned.
    :returns: A list of dicts with data on the tasks.
    """
    return IMPL.task_list(status=status)


def task_delete(uuid, status=None):
    """Delete a task.

    This method removes the task by the uuid, but if the status
    argument is specified, then the task is removed only when these
    statuses are equal otherwise an exception is raised.

    :param uuid: UUID of the task.
    :raises: :class:`rally.exceptions.TaskNotFound` if the task does not exist.
    :raises: :class:`rally.exceptions.TaskInvalidStatus` if the status
             of the task does not equal to the status argument.
    """
    return IMPL.task_delete(uuid, status=status)


def task_result_get_all_by_uuid(task_uuid):
    """Get list of task results.

    :param task_uuid: string with UUID of Task instance.
    :returns: list instances of TaskResult.
    """
    return IMPL.task_result_get_all_by_uuid(task_uuid)


def task_result_create(task_uuid, key, data):
    """Append result record to task.

    :param task_uuid: string with UUID of Task instance.
    :param key: key expected to update in task result.
    :param data: data expected to update in task result.
    :returns: TaskResult instance appended.
    """
    return IMPL.task_result_create(task_uuid, key, data)


def deployment_create(values):
    """Create a deployment from the values dictionary.

    :param values: dict with record values on the deployment.
    :returns: a dict with data on the deployment.
    """
    return IMPL.deployment_create(values)


def deployment_delete(uuid):
    """Delete a deployment by UUID.

    :param uuid: UUID of the deployment.
    :raises: :class:`rally.exceptions.DeploymentNotFound` if the deployment
             does not exist.
    :raises: :class:`rally.exceptions.DeploymentIsBusy` if the resource is
             not enough.
    """
    return IMPL.deployment_delete(uuid)


def deployment_get(uuid):
    """Get a deployment by UUID.

    :param uuid: UUID of the deployment.
    :raises: :class:`rally.exceptions.DeploymentNotFound` if the deployment
             does not exist.
    :returns: a dict with data on the deployment.
    """
    return IMPL.deployment_get(uuid)


def deployment_update(uuid, values):
    """Update a deployment by values.

    :param uuid: UUID of the deployment.
    :param values: dict with items to update.
    :raises: :class:`rally.exceptions.DeploymentNotFound` if the deployment
             does not exist.
    :returns: a dict with data on the deployment.
    """
    return IMPL.deployment_update(uuid, values)


def deployment_list(status=None, parent_uuid=None, name=None):
    """Get list of deployments.

    :param status: if None returns any deployments with any status.
    :param parent_uuid: filter by parent. If None, return only "root"
                        deployments.
    :param name: Name of deployment
    :returns: a list of dicts with data on the deployments.
    """
    return IMPL.deployment_list(status=status, parent_uuid=parent_uuid,
                                name=name)


def resource_create(values):
    """Create a resource from the values dictionary.

    :param values: a dict with data on the resource.
    :returns: a dict with updated data on the resource.
    """
    return IMPL.resource_create(values)


def resource_get_all(deployment_uuid, provider_name=None, type=None):
    """Return resources of a deployment.

    :param deployment_uuid: filter by uuid of a deployment
    :param provider_name: filter by provider_name, if is None, then
                          return all prorivders
    :param type: filter by type, if is None, then return all types
    :returns: a list of dicts with data on a resource
    """
    return IMPL.resource_get_all(deployment_uuid,
                                 provider_name=provider_name,
                                 type=type)


def resource_delete(id):
    """Delete a resource.

    :param id: ID of a resource.
    :raises: :class:`rally.exceptions.ResourceNotFound` if the resource
             does not exist.
    """
    return IMPL.resource_delete(id)


def verification_create(deployment_uuid):
    """Create Verification record in DB.

    :param deployment_uuid: UUID of the deployment.
    :returns: a dict with verification data.
    """
    return IMPL.verification_create(deployment_uuid)


def verification_get(verification_uuid):
    """Returns verification by UUID.

    :param id: UUID of the verification.
    :raises: :class:`rally.exceptions.NotFoundException` if verification
             does not exist.
    :returns: a dict with verification data.
    """
    return IMPL.verification_get(verification_uuid)


def verification_delete(verification_uuid):
    """Delete verification.

    :param verification_uuid: UUID of the verification.
    :raises: :class:`rally.exceptions.NotFoundException` if verification
             does not exist.
    """
    return IMPL.verification_delete(verification_uuid)


def verification_update(uuid, values):
    """Update verification by values.

    :param uuid: UUID of the verification.
    :param values: dict with record values.
    :raises: :class:`rally.exceptions.NotFoundException` if verification
             does not exist.
    :returns: new updated task dict with data on the task.
    """
    return IMPL.verification_update(uuid, values)


def verification_list(status=None):
    """Get a list of verifications.

    :param status: Verification status to filter the returned list on.
    :returns: A list of dicts with data on the verifications.
    """
    return IMPL.verification_list(status=status)


def verification_result_get(verification_uuid):
    """Get dict of verification results.

    :param verification_uuid: string with UUID of Verification instance.
    :returns: dict instance of VerificationResult.
    """
    return IMPL.verification_result_get(verification_uuid)


def verification_result_create(verification_uuid, values):
    """Append result record to verification.

    :param verification_uuid: string with UUID of Verification instance.
    :param values: dict with record values.
    :returns: TaskResult instance appended.
    """
    return IMPL.verification_result_create(verification_uuid, values)
