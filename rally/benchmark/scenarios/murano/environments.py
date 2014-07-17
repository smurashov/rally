from rally.benchmark.scenarios.murano import utils
from rally.openstack.common import log as logging
from rally.benchmark.scenarios import base


LOG = logging.getLogger(__name__)


class MuranoEnvironments(utils.MuranoScenario):

    def __init__(self, *args, **kwargs):
        super(MuranoEnvironments, self).__init__(*args, **kwargs)

    @base.scenario(context={"cleanup": ["murano"]})
    def get_list_environments(self):
        environment = self._create_environment(self._generate_random_name())
        self._list_environments()
        self._create_session(environment.id)
        self._delete_environment(environment.id)
