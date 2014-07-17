from oslo.config import cfg

from rally.benchmark.scenarios import base
from rally.benchmark.scenarios import utils as scenario_utils


class MuranoScenario(base.Scenario):

    @scenario_utils.atomic_action_timer('murano.list_environments')
    def _list_environments(self):

        return self.clients('murano').environments.list()

    @scenario_utils.atomic_action_timer('murano.create_environment')
    def _create_environment(self, environment_name):

        body = {'name': environment_name}

        return self.clients('murano').environments.create(body)

    @scenario_utils.atomic_action_timer('murano.delete_environment')
    def _delete_environment(self, environment_id):

        return self.clients('murano').environments.delete(environment_id)

    @scenario_utils.atomic_action_timer('murano.create_session')
    def _create_session(self, environment_id):

        return self.clients('murano').sessions.configure(environment_id)
