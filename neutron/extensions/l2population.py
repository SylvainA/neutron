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

import abc

from neutron.api import extensions
from neutron.api.v2 import attributes as attr
from neutron.api.v2 import base
from neutron.common import exceptions as qexception
from neutron import manager
from neutron.openstack.common import log as logging
from neutron.plugins.common import constants
from neutron.services import service_base

LOG = logging.getLogger(__name__)


class L2populationEntryNotFound(qexception.NotFound):
    message = _("L2 Forward entry %(entry_id)s does not exist")


RESOURCE_ATTRIBUTE_MAP = {
    'l2_fdb_entries': {
        'id': {'allow_post': False, 'allow_put': False,
               'is_visible': True,
               'primary_key': True},
        'port_id': {'allow_post': True, 'allow_put': False,
                    'required_by_policy': True,
                    'is_visible': True},
        'segment_id': {'allow_post': True, 'allow_put': False,
                       'required_by_policy': True,
                       'is_visible': True},
        'agent_id': {'allow_post': True, 'allow_put': False,
                     'required_by_policy': True,
                     'is_visible': True}
    }
}


class L2population(extensions.ExtensionDescriptor):

    @classmethod
    def get_name(cls):
        return "Neutron L2population"

    @classmethod
    def get_alias(cls):
        return "l2population"

    @classmethod
    def get_description(cls):
        return "Neutron L2population extension."

    @classmethod
    def get_namespace(cls):
        return "http://wiki.openstack.org/wiki/Neutron/L2population#API"

    @classmethod
    def get_updated(cls):
        return "2013-07-22T10:00:00-00:00"

    @classmethod
    def get_plugin_interface(cls):
        return L2populationPluginBase

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""

        my_plurals = [(key, key[:-3] + 'i')
                      for key in RESOURCE_ATTRIBUTE_MAP.keys()]
        attr.PLURALS.update(dict(my_plurals))
        exts = []
        plugin = manager.NeutronManager.get_service_plugins()[
            constants.L2POPULATION]
        for resource_name in ['l2_fdb_entry']:
            collection_name = resource_name.replace('y', 'ies')

            collection_name = collection_name.replace('_', '-')
            params = RESOURCE_ATTRIBUTE_MAP.get(resource_name.replace('y',
                                                                      'ies'),
                                                dict())

            controller = base.create_resource(collection_name,
                                              resource_name,
                                              plugin, params, allow_bulk=True,
                                              allow_pagination=True,
                                              allow_sorting=True)

            ex = extensions.ResourceExtension(
                collection_name,
                controller,
                path_prefix=constants.COMMON_PREFIXES[constants.L2POPULATION],
                attr_map=params)
            exts.append(ex)

        return exts

    def update_attributes_map(self, attributes):
        super(L2population, self).update_attributes_map(
            attributes, extension_attrs_map=RESOURCE_ATTRIBUTE_MAP)

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        else:
            return {}


class L2populationPluginBase(service_base.ServicePluginBase):
    __metaclass__ = abc.ABCMeta

    def get_plugin_name(self):
        return constants.L2POPULATION

    def get_plugin_description(self):
        return constants.L2POPULATION

    def get_plugin_type(self):
        return constants.L2POPULATION

    @abc.abstractmethod
    def create_fdb_entry(self, context, entry):
        """Create an entry to the forwarding table."""
        pass

    @abc.abstractmethod
    def delete_fdb_entry(self, context, entry_id):
        """Delete forwarding table entry."""
        pass

    @abc.abstractmethod
    def get_fdb_entry(self, context, entry_id, fields=None):
        """Get a forwarding table entry."""
        pass

    @abc.abstractmethod
    def get_fdb_entries(self, context, filters=None, fields=None,
                        sorts=None, limit=None, marker=None,
                        page_reverse=False):
        """List forwarding table entries."""
        pass
