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

import sqlalchemy as sa
from sqlalchemy import orm

from neutron.common import exceptions as q_exc
from neutron.db import agents_db
from neutron.db import api as dbapi
from neutron.db import db_base_plugin_v2 as base_db
from neutron.db import model_base
from neutron.db import models_v2
from neutron.extensions import agent as ext_agent
from neutron.extensions import l2population as ext_l2population
from neutron.openstack.common import log as logging
from neutron.openstack.common import uuidutils
from neutron.plugins.ml2 import models as models_ml2

LOG = logging.getLogger(__name__)


class L2populationForwardDB(model_base.BASEV2, models_v2.HasId):
    port_id = sa.Column(sa.String(36),
                        sa.ForeignKey("ports.id",
                                      ondelete="CASCADE"),
                        nullable=False)
    segment_id = sa.Column(sa.String(36),
                           sa.ForeignKey("ml2_network_segments.id",
                                         ondelete="CASCADE"),
                           nullable=False)
    agent_id = sa.Column(sa.String(36),
                         sa.ForeignKey("agents.id",
                                       ondelete="CASCADE"),
                         nullable=False)

    port = orm.relationship(
        models_v2.Port,
        backref=orm.backref("l2PopulationForwardDB",
                            lazy='joined',
                            cascade='delete'))
    segment = orm.relationship(
        models_ml2.NetworkSegment,
        backref=orm.backref("l2PopulationForwardDB",
                            lazy='joined',
                            cascade='delete'))
    agent = orm.relationship(
        agents_db.Agent,
        backref=orm.backref("l2PopulationForwardDB",
                            lazy='joined',
                            cascade='delete'))


class L2populationForwardDbMixin(ext_l2population.L2populationPluginBase,
                                 base_db.CommonDbMixin):

    def __init__(self):
        dbapi.register_models()

#        self.l2_fdb_rpc = l2population_rpc_agent_api.L2populationAgentNotifyAPI()

    def _make_fdb_entry_dict(self, entry, fields=None):
        res = {'id': entry['id'],
               'port_id': entry['port_id'],
               'segment_id': entry['segment_id'],
               'agent_id': entry['agent_id']}
        return self._fields(res, fields)

    def create_fdb_entry(self, context, entry):
        m = entry['l2_fdb_entry']
        with context.session.begin(subtransactions=True):
            try:
                port = self._get_by_id(context, models_v2.Port, m['port_id'])
            except orm.exc.NoResultFound:
                raise q_exc.PortNotFound(port_id=id, net_id=None)

            try:
                segment = self._get_by_id(context, models_ml2.NetworkSegment,
                                          m['segment_id'])
            except orm.exc.NoResultFound:
                raise

            try:
                agent = self._get_by_id(context, agents_db.Agent,
                                        m['agent_id'])
            except orm.exc.NoResultFound:
                raise ext_agent.AgentNotFound(id=m['agent_id'])

            entry_db = L2populationForwardDB(id=uuidutils.generate_uuid(),
                                             port_id=port['id'],
                                             segment_id=segment['id'],
                                             agent_id=agent['id'])
            context.session.add(entry_db)

        return self._make_fdb_entry_dict(entry_db)

    def delete_fdb_entry(self, context, entry_id):
        with context.session.begin(subtransactions=True):
            try:
                entry = self._get_by_id(context, L2populationForwardDB,
                                        entry_id)
            except orm.exc.NoResultFound:
                raise ext_l2population.L2populationEntryNotFound(entry_id)

            context.session.delete(entry)

    def get_fdb_entry(self, context, entry_id, fields=None):
        try:
            entry = self._get_by_id(context, L2populationForwardDB,
                                    entry_id)
        except orm.exc.NoResultFound:
            raise ext_l2population.L2populationEntryNotFound(entry_id)

        return self._make_fdb_entry_dict(entry)

    def get_fdb_entries(self, context, filters=None, fields=None,
                        sorts=None, limit=None, marker=None,
                        page_reverse=False):
        marker_obj = self._get_marker_obj(context, 'l2_fdb_entries', limit,
                                          marker)
        return self._get_collection(context, L2populationForwardDB,
                                    self._make_fdb_entry_dict,
                                    filters=filters, fields=fields,
                                    sorts=sorts,
                                    limit=limit,
                                    marker_obj=marker_obj,
                                    page_reverse=page_reverse)
