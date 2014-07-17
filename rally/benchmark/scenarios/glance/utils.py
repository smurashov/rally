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

import os
from oslo.config import cfg
import time

from rally.benchmark.scenarios import base
from rally.benchmark.scenarios import utils as scenario_utils
from rally.benchmark import utils as bench_utils


glance_benchmark_opts = [
    cfg.FloatOpt('glance_image_create_prepoll_delay',
                 default=2.0,
                 help='Time to sleep after creating a resource before '
                      'polling for it status'),
    cfg.FloatOpt('glance_image_create_timeout',
                 default=120.0,
                 help='Time to wait for glance image to be created.'),
    cfg.FloatOpt('glance_image_create_poll_interval',
                 default=1.0,
                 help='Interval between checks when waiting for image '
                      'creation.'),
    cfg.FloatOpt('glance_image_delete_timeout',
                 default=120.0,
                 help='Time to wait for glance image to be deleted.'),
    cfg.FloatOpt('glance_image_delete_poll_interval',
                 default=1.0,
                 help='Interval between checks when waiting for image '
                      'deletion.')
]


CONF = cfg.CONF
benchmark_group = cfg.OptGroup(name='benchmark', title='benchmark options')
CONF.register_opts(glance_benchmark_opts, group=benchmark_group)


class GlanceScenario(base.Scenario):

    @scenario_utils.atomic_action_timer('glance.list_images')
    def _list_images(self):
        """Returns user images list."""

        return list(self.clients("glance").images.list())

    @scenario_utils.atomic_action_timer('glance.create_image')
    def _create_image(self, image_name, container_format,
                      image_location, disk_format, **kwargs):
        """Create a new image.

        :param image_name: String used to name the image
        :param container_format: Container format of image.
        Acceptable formats: ami, ari, aki, bare, and ovf.
        :param image_location: image file location used to upload
        :param disk_format: Disk format of image. Acceptable formats:
        ami, ari, aki, vhd, vmdk, raw, qcow2, vdi, and iso.
        :param **kwargs:  optional parameters to create image

        returns: object of image
        """

        kw = {
            "name": image_name,
            "container_format": container_format,
            "disk_format": disk_format,
        }

        kw.update(kwargs)

        if os.path.isfile(image_location):
            #TODO(chen): around that live with open()
            # probably can cause issue with too many open fd
            kw["data"] = open(image_location)
        else:
            kw["copy_from"] = image_location

        image = self.clients("glance").images.create(**kw)

        time.sleep(CONF.benchmark.glance_image_create_prepoll_delay)

        image = bench_utils.wait_for(
            image,
            is_ready=bench_utils.resource_is("active"),
            update_resource=bench_utils.get_from_manager(),
            timeout=CONF.benchmark.glance_image_create_timeout,
            check_interval=CONF.benchmark.glance_image_create_poll_interval)

        if "data" in kw:
            kw["data"].close()

        return image

    @scenario_utils.atomic_action_timer('glance.delete_image')
    def _delete_image(self, image):
        """Deletes the given image.

        Returns when the image is actually deleted.

        :param image: Image object
        """
        image.delete()
        bench_utils.wait_for_delete(
            image,
            update_resource=bench_utils.get_from_manager(),
            timeout=CONF.benchmark.glance_image_delete_timeout,
            check_interval=CONF.benchmark.glance_image_delete_poll_interval)
