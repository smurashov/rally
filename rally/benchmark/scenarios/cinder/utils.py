# Copyright 2013 Huawei Technologies Co.,LTD.
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

from oslo.config import cfg
import time

from rally.benchmark.scenarios import base
from rally.benchmark.scenarios import utils as scenario_utils
from rally.benchmark import utils as bench_utils


cinder_benchmark_opts = [
    cfg.FloatOpt('cinder_volume_create_prepoll_delay',
                 default=2.0,
                 help='Time to sleep after creating a resource before'
                      ' polling for it status'),
    cfg.FloatOpt('cinder_volume_create_timeout',
                 default=600.0,
                 help='Time to wait for cinder volume to be created.'),
    cfg.FloatOpt('cinder_volume_create_poll_interval',
                 default=2.0,
                 help='Interval between checks when waiting for volume'
                      ' creation.'),
    cfg.FloatOpt('cinder_volume_delete_timeout',
                 default=600.0,
                 help='Time to wait for cinder volume to be deleted.'),
    cfg.FloatOpt('cinder_volume_delete_poll_interval',
                 default=2.0,
                 help='Interval between checks when waiting for volume'
                      ' deletion.')
]

CONF = cfg.CONF
benchmark_group = cfg.OptGroup(name='benchmark', title='benchmark options')
CONF.register_opts(cinder_benchmark_opts, group=benchmark_group)


class CinderScenario(base.Scenario):

    RESOURCE_NAME_PREFIX = "rally_volume_"

    @scenario_utils.atomic_action_timer('cinder.list_volumes')
    def _list_volumes(self, detailed=True):
        """Returns user volumes list."""

        return self.clients("cinder").volumes.list(detailed)

    @scenario_utils.atomic_action_timer('cinder.create_volume')
    def _create_volume(self, size, **kwargs):
        """create one volume.

        Returns when the volume is actually created and is in the "Available"
        state.

        :param size: int be size of volume in GB
        :param **kwargs: Other optional parameters to initialize the volume

        :returns: Created volume object
        """
        kwargs["display_name"] = kwargs.get("display_name",
                                            self._generate_random_name())
        volume = self.clients("cinder").volumes.create(size, **kwargs)
        # NOTE(msdubov): It is reasonable to wait 5 secs before starting to
        #                check whether the volume is ready => less API calls.
        time.sleep(CONF.benchmark.cinder_volume_create_prepoll_delay)
        volume = bench_utils.wait_for(
            volume,
            is_ready=bench_utils.resource_is("available"),
            update_resource=bench_utils.get_from_manager(),
            timeout=CONF.benchmark.cinder_volume_create_timeout,
            check_interval=CONF.benchmark.cinder_volume_create_poll_interval
        )
        return volume

    @scenario_utils.atomic_action_timer('cinder.delete_volume')
    def _delete_volume(self, volume):
        """Delete the given volume.

        Returns when the volume is actually deleted.

        :param volume: volume object
        """
        volume.delete()
        bench_utils.wait_for_delete(
            volume,
            update_resource=bench_utils.get_from_manager(),
            timeout=CONF.benchmark.cinder_volume_delete_timeout,
            check_interval=CONF.benchmark.cinder_volume_delete_poll_interval
        )
