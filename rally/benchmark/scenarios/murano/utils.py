import random
import uuid

from oslo.config import cfg

from rally.benchmark.scenarios import base
from rally.benchmark.scenarios import utils as scenario_utils
from rally.benchmark import utils as bench_utils


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

    @scenario_utils.atomic_action_timer('murano.create_service')
    def _add_app(self, environment_id, session_id, image_name, flavor_name):

        app = self._get_random_app(image_name, flavor_name)

        return self.clients('murano').services.post(environment_id, path='/',
                                                    data=app,
                                                    session_id=session_id)

    @scenario_utils.atomic_action_timer('murano.deploy_environment')
    def _deploy_environment(self, environment_id, session_id):

        return self.clients('murano').sessions.deploy(environment_id,
                                                      session_id)

    def _get_random_app(self, image_name, flavor_name):
        k = random.randint(0, 100)

        if k <= 33:
            return {
                "instance": {
                    "?": {
                        "type": "io.murano.resources.LinuxMuranoInstance",
                        "id": str(uuid.uuid4())
                    },
                    "flavor": flavor_name,
                    "image": image_name,
                    "name": "instance{0}".format(uuid.uuid4().hex[:5])
                },
                "name": "app{0}".format(uuid.uuid4().hex[:5]),
                "?": {
                    "type": "io.murano.apps.linux.Telnet",
                    "id": str(uuid.uuid4())
                }
            }

        elif k <= 66:
            return {
                "instance": {
                    "?": {
                        "type": "io.murano.resources.LinuxMuranoInstance",
                        "id": str(uuid.uuid4())
                    },
                    "flavor": flavor_name,
                    "image": image_name,
                    "name": "instance{0}".format(uuid.uuid4().hex[:5])
                },
                "name": "app{0}".format(uuid.uuid4().hex[:5]),
                "?": {
                    "type": "io.murano.apps.apache.Apache",
                    "id": str(uuid.uuid4())
                }
            }

        else:
            return {
                "instance": {
                    "?": {
                        "type": "io.murano.resources.LinuxMuranoInstance",
                        "id": str(uuid.uuid4())
                    },
                    "flavor": flavor_name,
                    "image": image_name,
                    "name": "instance{0}".format(uuid.uuid4().hex[:5])
                },
                "name": "app{0}".format(uuid.uuid4().hex[:5]),
                "?": {
                    "type": "io.murano.apps.PostgreSql",
                    "id": str(uuid.uuid4())
                }
            }

    @scenario_utils.atomic_action_timer('murano.wait_finish_of_deploy')
    def _wait_finish_of_deploy(self, environment):

        bench_utils.wait_for(
            environment, is_ready=bench_utils.resource_is("READY"),
            update_resource=bench_utils.get_from_manager(),
            timeout=1200.0,
            check_interval=5.0
        )

    @scenario_utils.atomic_action_timer('murano.get_deployments_list')
    def _get_deployments_list(self, environment_id):

        return self.clients('murano').deployments.list(environment_id)
