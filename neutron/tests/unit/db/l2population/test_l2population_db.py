# Copyright (c) 2012 OpenStack Foundation.
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
#
# @author: Sylvain Afchain, eNovance SAS
#

import contextlib
import logging
import os

import webob.exc

from neutron.api.extensions import ExtensionMiddleware
from neutron.api.extensions import PluginAwareExtensionManager
from neutron.common import config
from neutron import context
from neutron.db import agents_db
import neutron.extensions
from neutron.extensions import l2population
from neutron.plugins.common import constants
from neutron.services.l2population import l2population_plugin
from neutron.tests.unit import test_db_plugin

LOG = logging.getLogger(__name__)

DB_L2POPULATION_PLUGIN_KLASS = (
    "neutron.services.l2population."
    "l2population_plugin.L2populationPlugin"
)
ROOTDIR = os.path.dirname(__file__) + '../../../..'
ETCDIR = os.path.join(ROOTDIR, 'etc')

extensions_path = ':'.join(neutron.extensions.__path__)


def etcdir(*p):
    return os.path.join(ETCDIR, *p)


class L2populationPluginDbTestCaseMixin(object):
    def _create_fdb_entry(self, fmt, port_id, segment_id, agent_id, **kwargs):
        data = {'l2_fdb_entry': {'port_id': port_id,
                                 'segment_id': segment_id,
                                 'agent_id': agent_id}}
        req = self.new_create_request('l2-fdb-entry', data,
                                      fmt)

        req.environ['neutron.context'] = context.get_admin_context()

        return req.get_response(self.ext_api)

    def _make_fdb_entry(self, fmt, port_id, segment_id, agent_id, **kwargs):
        res = self._create_fdb_entry(fmt, port_id, segment_id,
                                     agent_id, **kwargs)
        if res.status_int >= 400:
            raise webob.exc.HTTPClientError(code=res.status_int)
        return self.deserialize(fmt, res)

    @contextlib.contextmanager
    def fdb_entry(self, port_id, segment_id, agent_id,
                  fmt=None, no_delete=False, **kwargs):
        if not fmt:
            fmt = self.fmt
        fdb_entry = self._make_fdb_entry(fmt, port_id, segment_id, agent_id,
                                         **kwargs)
        try:
            yield fdb_entry
        finally:
            if not no_delete:
                self._delete('l2-fdb-entries',
                             fdb_entry['l2_fdb_entry']['id'])


class L2populationPluginDbTestCase(test_db_plugin.NeutronDbPluginV2TestCase,
                                   L2populationPluginDbTestCaseMixin):
    fmt = 'json'

    resource_prefix_map = dict(
        (k.replace('_', '-'),
         constants.COMMON_PREFIXES[constants.L2POPULATION])
        for k in l2population.RESOURCE_ATTRIBUTE_MAP.keys()
    )

    def setUp(self, plugin=None):
        service_plugins = {
            'l2population_plugin_name': DB_L2POPULATION_PLUGIN_KLASS
        }

        super(L2populationPluginDbTestCase, self).setUp(
            plugin=plugin,
            service_plugins=service_plugins
        )

        self.plugin = l2population_plugin.L2populationPlugin()
        ext_mgr = PluginAwareExtensionManager(
            extensions_path,
            {constants.L2POPULATION: self.plugin}
        )
        app = config.load_paste_app('extensions_test_app')
        self.ext_api = ExtensionMiddleware(app, ext_mgr=ext_mgr)

    def test_create_fdb_entry(self):
        keys = [('name', None,), ('description', None)]
        segment_id = 123
        agent_id = 456
        with self.port() as port:
            port_id = port['port']['id']
            with self.fdb_entry(port_id, segment_id, agent_id) as fdb_entry:
                for k, v, in keys:
                    self.assertEqual(fdb_entry['l2_fdb_entry'][k], v)
