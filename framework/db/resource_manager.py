from framework.db import models
from framework.config import config
from framework.lib.general import cprint
import os
import logging


class ResourceDB(object):
    def __init__(self, Core):
        self.Core = Core
        self.LoadResourceDBFromFile(self.Core.Config.FrameworkConfigGet("DEFAULT_RESOURCES_PROFILE"))

    def LoadResourceDBFromFile(self, file_path): # This needs to be a list instead of a dictionary to preserve order in python < 2.7
        logging.info("Loading Resources from: " + file_path + " ..")
        resources = self.GetResourcesFromFile(file_path)
        # Delete all old resources which are not edited by user
        # because we may have updated the resource
        self.Core.DB.session.query(models.Resource).filter_by(dirty=False).delete()
        # resources = [(Type, Name, Resource), (Type, Name, Resource),]
        for Type, Name, Resource in resources:
            # Need more filtering to avoid duplicates
            if not self.Core.DB.session.query(models.Resource).filter_by(resource_type = Type, resource_name = Name, resource = Resource).all():
                self.Core.DB.session.add(models.Resource(resource_type = Type, resource_name = Name, resource = Resource))
        self.Core.DB.session.commit()

    def GetResourcesFromFile(self, resource_file):
        resources = []
        ConfigFile = self.Core.open(resource_file, 'r').read().splitlines() # To remove stupid '\n' at the end
        for line in ConfigFile:
            if '#' == line[0]:
                continue # Skip comment lines
            try:
                Type, Name, Resource = line.split('_____')
                # Resource = Resource.strip()
                resources.append((Type, Name, Resource))
            except ValueError:
                cprint("ERROR: The delimiter is incorrect in this line at Resource File: "+str(line.split('_____')))
        return resources

    def GetReplacementDict(self):
        configuration = self.Core.DB.Config.GetReplacementDict()
        configuration.update(self.Core.DB.Target.GetTargetConfig())
        configuration.update(self.Core.Config.GetReplacementDict())
        return configuration

    def GetRawResources(self, ResourceType):
        filter_query = self.Core.DB.session.query(models.Resource.resource_name, models.Resource.resource).filter_by(resource_type = ResourceType)
        # Sorting is necessary for working of ExtractURLs, since it must run after main command, so order is imp
        sort_query = filter_query.order_by(models.Resource.id)
        raw_resources = sort_query.all()
        return raw_resources

    def GetResources(self, ResourceType):
        replacement_dict = self.GetReplacementDict()
        raw_resources = self.GetRawResources(ResourceType)
        resources = []
        for name, resource in raw_resources:
            resources.append([name, self.Core.Config.MultipleReplace(resource, replacement_dict)])
        return resources

    def GetRawResourceList(self, ResourceList):
        raw_resources = self.Core.DB.session.query(models.Resource.resource_name, models.Resource.resource).filter(models.Resource.resource_type.in_(ResourceList)).all()
        return raw_resources

    def GetResourceList(self, ResourceTypeList):
        replacement_dict = self.GetReplacementDict()
        raw_resources = self.GetRawResourceList(ResourceTypeList)
        resources = []
        for name, resource in raw_resources:
            resources.append([name, self.Core.Config.MultipleReplace(resource, replacement_dict)])
        return resources
