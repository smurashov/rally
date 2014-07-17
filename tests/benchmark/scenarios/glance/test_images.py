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

import mock

from rally.benchmark.scenarios.glance import images
from rally.benchmark.scenarios.nova import servers
from rally.objects import endpoint
from rally import osclients
from tests import fakes
from tests import test

GLANCE_IMAGES = "rally.benchmark.scenarios.glance.images.GlanceImages"


class GlanceImagesTestCase(test.TestCase):

    @mock.patch(GLANCE_IMAGES + "._generate_random_name")
    @mock.patch(GLANCE_IMAGES + "._list_images")
    @mock.patch(GLANCE_IMAGES + "._create_image")
    def test_create_and_list_image(self, mock_create, mock_list,
                                   mock_random_name):
        glance_scenario = images.GlanceImages()
        mock_random_name.return_value = "test-rally-image"
        glance_scenario.create_and_list_image("cf", "url", "df",
                                              fakearg="f")
        mock_create.assert_called_once_with("test-rally-image", "cf",
                                            "url", "df", fakearg="f")
        mock_list.assert_called_once_with()

    @mock.patch(GLANCE_IMAGES + "._generate_random_name")
    @mock.patch(GLANCE_IMAGES + "._delete_image")
    @mock.patch(GLANCE_IMAGES + "._create_image")
    def test_create_and_delete_image(self, mock_create, mock_delete,
                                     mock_random_name):
        glance_scenario = images.GlanceImages()
        fake_image = object()
        mock_create.return_value = fake_image
        mock_random_name.return_value = "test-rally-image"
        glance_scenario.create_and_delete_image("cf", "url", "df",
                                                fakearg="f")

        mock_create.assert_called_once_with("test-rally-image", "cf",
                                            "url", "df", fakearg="f")
        mock_delete.assert_called_once_with(fake_image)

    @mock.patch(GLANCE_IMAGES + "._generate_random_name")
    @mock.patch(GLANCE_IMAGES + "._boot_servers")
    @mock.patch(GLANCE_IMAGES + "._create_image")
    @mock.patch("rally.benchmark.runners.base.osclients")
    def test_create_image_and_boot_instances(self,
                                             mock_osclients,
                                             mock_create_image,
                                             mock_boot_servers,
                                             mock_random_name):
        glance_scenario = images.GlanceImages()
        nova_scenario = servers.NovaServers()
        fc = fakes.FakeClients()
        mock_osclients.Clients.return_value = fc
        fake_glance = fakes.FakeGlanceClient()
        fc.glance = lambda: fake_glance
        fake_nova = fakes.FakeNovaClient()
        fc.nova = lambda: fake_nova
        user_endpoint = endpoint.Endpoint("url", "user", "password", "tenant")
        nova_scenario._clients = osclients.Clients(user_endpoint)
        fake_image = fakes.FakeImage()
        fake_servers = [object() for i in range(5)]
        mock_create_image.return_value = fake_image
        mock_boot_servers.return_value = fake_servers
        mock_random_name.return_value = "random_name"
        kwargs = {'fakearg': 'f'}
        with mock.patch("rally.benchmark.scenarios.glance.utils.time.sleep"):
            glance_scenario.\
                create_image_and_boot_instances("cf", "url", "df",
                                                "fid", 5, **kwargs)
            mock_create_image.assert_called_once_with("random_name", "cf",
                                                      "url", "df", **kwargs)
            mock_boot_servers.assert_called_once_with("random_name",
                                                      "image-id-0",
                                                      "fid", 5, **kwargs)
