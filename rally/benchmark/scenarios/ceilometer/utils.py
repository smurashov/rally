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

import uuid

from rally.benchmark.scenarios import base
from rally.benchmark.scenarios import utils as scenario_utils


class CeilometerScenario(base.Scenario):
    """This class should contain base operations for benchmarking Ceilometer,
    most of them are GET/PUT/POST/DELETE Api calls.
    """
    RESOURCE_NAME_PREFIX = "rally_ceilometer_"

    def _get_alarm_dict(self, **kwargs):
        """Prepares and returns alarm dictionary for creating an alarm.

        :param kwargs: optional parameters to create alarm
        :returns: alarm dictionary used to create an alarm
        """
        # TODO(Aswad): Reuse _generate_random_name from base.Scenario instead
        # of generating alarm_uuid. Ref: bp/benchmark-scenarios-for-neutron.
        alarm_uuid = str(uuid.uuid4())
        alarm = {"alarm_id": alarm_uuid,
                 "name": "TestAlarm-%s" % alarm_uuid,
                 "description": "Test Alarm"}

        alarm.update(kwargs)
        return alarm

    @scenario_utils.atomic_action_timer('ceilometer.list_alarms')
    def _list_alarms(self, alarm_id=None):
        """List alarms.

        List alarm matching alarm_id. It fetches all alarms
        if alarm_id is None.
        :param alarm_id: specifies id of the alarm
        :returns: list of alarms
        """
        if alarm_id:
            return self.clients("ceilometer").alarms.get(alarm_id)
        else:
            return self.clients("ceilometer").alarms.list()

    @scenario_utils.atomic_action_timer('ceilometer.create_alarm')
    def _create_alarm(self, meter_name, threshold, kwargs):
        """Create an alarm.

        :param meter_name: specifies meter name of the alarm
        :param threshold: specifies alarm threshold
        :param kwargs: contains optional features of alarm to be created
        :returns: alarm
        """
        kwargs.update({"meter_name": meter_name,
                       "threshold": threshold})
        alarm_dict = self._get_alarm_dict(**kwargs)
        alarm = self.clients("ceilometer").alarms.create(**alarm_dict)
        return alarm

    @scenario_utils.atomic_action_timer('ceilometer.delete_alarm')
    def _delete_alarm(self, alarm_id):
        """Deletes an alarm.

        :param alarm_id: specifies id of the alarm
        """
        self.clients("ceilometer").alarms.delete(alarm_id)

    @scenario_utils.atomic_action_timer('ceilometer.update_alarm')
    def _update_alarm(self, alarm_id, alarm_dict_delta):
        """Updates an alarm.

        :param alarm_id: specifies id of the alarm
        :param alarm_dict_delta: features of alarm to be updated
        """
        self.clients("ceilometer").alarms.update(alarm_id, **alarm_dict_delta)

    @scenario_utils.atomic_action_timer('ceilometer.get_meters')
    def _list_meters(self):
        """Get list of user's meters."""
        return self.clients("ceilometer").meters.list()

    @scenario_utils.atomic_action_timer('ceilometer.list_resources')
    def _list_resources(self):
        """List all resources.

        :returns: list of all resources
        """
        return self.clients("ceilometer").resources.list()

    @scenario_utils.atomic_action_timer('ceilometer.get_stats')
    def _get_stats(self, meter_name):
        """Get stats for a specific meter.

        :param meter_name: Name of ceilometer meter
        """
        return self.clients("ceilometer").statistics.list(meter_name)

    @scenario_utils.atomic_action_timer('ceilometer.create_meter')
    def _create_meter(self, **kwargs):
        """Create a new meter.

        :param name_length: Length of meter name to be generated
        :param kwargs: Contains the optional attributes for meter creation
        :returns: Newly created meter
        """
        name = self._generate_random_name()
        samples = self.clients("ceilometer").samples.create(
            counter_name=name, **kwargs)
        return samples[0]
