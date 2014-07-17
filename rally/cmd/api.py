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

""" The Rally Service API. """

import logging
import os
import sys
from wsgiref import simple_server

from oslo.config import cfg

from rally.api import app as rally_app
from rally.openstack.common.gettextutils import _  # noqa
from rally.openstack.common import log


CONF = cfg.CONF
LOG = log.getLogger(__name__)


def main():
    # Initialize configuation and logging.
    CONF(sys.argv[1:], project='rally')
    log.setup('rally')
    # Prepare application and bind to the service socket.
    host = CONF.api.host
    port = CONF.api.port
    app = rally_app.make_app()
    server = simple_server.make_server(host, port, app)
    # Start application.
    LOG.info(_('Starting server in PID %s') % os.getpid())
    LOG.info(_("Configuration:"))
    CONF.log_opt_values(LOG, logging.INFO)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
