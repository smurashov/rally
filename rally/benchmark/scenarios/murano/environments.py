from rally.benchmark.scenarios.murano import utils
from rally.openstack.common import log as logging
from rally.benchmark.scenarios import base
from rally import exceptions as rally_exceptions

LOG = logging.getLogger(__name__)


class MuranoEnvironments(utils.MuranoScenario):

    def __init__(self, *args, **kwargs):
        super(MuranoEnvironments, self).__init__(*args, **kwargs)

    @base.scenario()
    def get_list_environments(self):
        self._list_environments()

    @base.scenario(context={"cleanup": ["murano"]})
    def create_environment_create_session_delete_environment(self):
        environment = self._create_environment(self._generate_random_name())

        self._create_session(environment.id)
        self._delete_environment(environment.id)

    @base.scenario(context={"cleanup": ["murano"]})
    def deploy_environment(self, image_name, flavor_name):
        environment = self._create_environment(self._generate_random_name())
        session = self._create_session(environment.id)

        self._add_app(environment.id, session.id, image_name, flavor_name)
        self._deploy_environment(environment.id, session.id)
        self._wait_finish_of_deploy(environment)

        deployment = self._get_deployments_list(environment.id)[-1]
        assert deployment.state == 'success'
        ip = environment.services[-1]['instance']['floatingIpAddress']
        self._check_port_access(ip, 23)

        self._delete_environment(environment.id)
