..
      Copyright 2014 Mirantis Inc. All Rights Reserved.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

.. _deploy:

The Deployment Layer
====================

Represents a set of deployment engines. An each deployment engine provide some
kind of technique of installation of OpenStack. Also there is an abstract base
class of deployment engine.

The :mod:`rally.deploy.engine` Module
-------------------------------------

.. automodule:: rally.deploy.engine
    :members:
    :undoc-members:
    :show-inheritance:

The DevStack Engine
-------------------

The :mod:`rally.deploy.engines.devstack` Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: rally.deploy.engines.devstack
    :members:
    :undoc-members:
    :show-inheritance:

The Dummy Engine
----------------

The :mod:`rally.deploy.engines.dummy` Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: rally.deploy.engines.dummy
    :members:
    :undoc-members:
    :show-inheritance:
