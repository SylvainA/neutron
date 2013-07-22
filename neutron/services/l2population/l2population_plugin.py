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

from neutron.common import rpc as p_rpc
from neutron.common import topics
from neutron.db.l2population import l2population_db
from neutron.openstack.common import rpc


class L2populationCallbacks(l2population_db.L2populationForwardDbMixin):

    RPC_API_VERSION = '1.0'

    def __init__(self, plugin):
        self.plugin = plugin

    def create_rpc_dispatcher(self):
        return p_rpc.PluginRpcDispatcher([self])

    def get_fdb_entries(self, context, **kwargs):
        return super(L2populationCallbacks, self).get_fdb_entries(context)


class L2populationPlugin(l2population_db.L2populationForwardDbMixin):
    """Implementation of the Neutron L2 Population Service Plugin."""
    supported_extension_aliases = ["l2population"]

    def __init__(self):
        super(L2populationPlugin, self).__init__()

        self.callbacks = L2populationCallbacks(self)

        self.conn = rpc.create_connection(new=True)
        self.conn.create_consumer(
            topics.L2POPULATION_AGENT,
            self.callbacks.create_rpc_dispatcher(),
            fanout=False)
        self.conn.consume_in_thread()
