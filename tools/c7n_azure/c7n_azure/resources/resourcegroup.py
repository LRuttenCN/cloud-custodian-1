# Copyright 2018 Capital One Services, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from c7n_azure.provider import resources
from c7n_azure.resources.arm import ArmResourceManager
from c7n_azure.utils import ResourceIdParser

from c7n.actions import BaseAction
from c7n.filters import Filter
from c7n.utils import type_schema


@resources.register('resourcegroup')
class ResourceGroup(ArmResourceManager):

    class resource_type(ArmResourceManager.resource_type):
        service = 'azure.mgmt.resource'
        client = 'ResourceManagementClient'
        enum_spec = ('resource_groups', 'list', None)

    def get_resources(self, resource_ids):
        resource_client = self.get_client('azure.mgmt.resource.ResourceManagementClient')
        data = [
            resource_client.resource_groups.get(ResourceIdParser.get_resource_group(rid))
            for rid in resource_ids
        ]
        return [r.serialize(True) for r in data]

    def augment(self, resources):
        for resource in resources:
            resource['type'] = 'Microsoft.Resources/subscriptions/resourceGroups'
        return resources


@ResourceGroup.filter_registry.register('empty-group')
class EmptyGroup(Filter):
    # policies:
    #   - name: test - azure
    #   resource: azure.resourcegroup
    #   filters:
    #       - type: empty-group

    def __call__(self, group):
        resources_iterator = (
            self.manager
                .get_client()
                .resources
                .list_by_resource_group(group['name'])
        )
        return not any(True for _ in resources_iterator)


@ResourceGroup.action_registry.register('delete')
class DeleteResourceGroup(BaseAction):
    # policies:
    #   - name: test - azure
    #   resource: azure.resourcegroup
    #   actions:
    #       - type: delete

    schema = type_schema('delete')

    def process(self, groups):
        for group in groups:
            self.manager.log.info('Removing resource group ' + group['name'])
            self.manager.get_client().resource_groups.delete(group['name'])
