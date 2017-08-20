import os
import logging

from owtf.utils import FileOperations
from owtf.db import models
from owtf.dependency_management.dependency_resolver import BaseComponent
from owtf.dependency_management.interfaces import ResourceInterface
from owtf.lib.general import cprint


class ResourceDB(BaseComponent, ResourceInterface):

    COMPONENT_NAME = "resource"

    def __init__(self):
        self.register_in_service_locator()
        self.config = self.get_component("config")
        self.db_config = self.get_component("db_config")
        self.target = self.get_component("target")
        self.db = self.get_component("db")
        self.error_handler = self.get_component("error_handler")

    def init(self):
        self.LoadResourceDBFromFile(self.config.get_profile_path("RESOURCES_PROFILE"))

    # This needs to be a list instead of a dictionary to preserve order in python < 2.7
    def LoadResourceDBFromFile(self, file_path):
        file_path = self.config.select_user_or_default_config_path(file_path)
        logging.info("Loading Resources from: %s..", file_path)
        if not os.path.isfile(file_path):  # check if the resource file exists
            self.error_handler.abort_framework("Resource file not found at: %s" % file_path)
        resources = self.GetResourcesFromFile(file_path)
        # Delete all old resources which are not edited by user
        # because we may have updated the resource
        self.db.session.query(models.Resource).filter_by(dirty=False).delete()
        for Type, Name, Resource in resources:
            self.db.session.add(models.Resource(resource_type=Type, resource_name=Name, resource=Resource))
        self.db.session.commit()

    def GetResourcesFromFile(self, resource_file):
        resources = set()
        ConfigFile = FileOperations.open(resource_file, 'r').read().splitlines()  # To remove stupid '\n' at the end
        for line in ConfigFile:
            if '#' == line[0]:
                continue  # Skip comment lines
            try:
                Type, Name, Resource = line.split('_____')
                resources.add((Type, Name, Resource))
            except ValueError:
                cprint("ERROR: The delimiter is incorrect in this line at Resource File: %s" % str(line.split('_____')))
        return resources

    def GetReplacementDict(self):
        configuration = self.db_config.GetReplacementDict()
        configuration.update(self.target.GetTargetConfig())
        configuration.update(self.config.GetReplacementDict())
        configuration.update(self.config.GetFrameworkConfigDict()) # for aux plugins
        return configuration

    def GetRawResources(self, ResourceType):
        filter_query = self.db.session.query(models.Resource.resource_name, models.Resource.resource).filter_by(
            resource_type=ResourceType)
        # Sorting is necessary for working of ExtractURLs, since it must run after main command, so order is imp
        sort_query = filter_query.order_by(models.Resource.id)
        raw_resources = sort_query.all()
        return raw_resources

    def GetResources(self, ResourceType):
        replacement_dict = self.GetReplacementDict()
        raw_resources = self.GetRawResources(ResourceType)
        resources = []
        for name, resource in raw_resources:
            resources.append([name, self.config.MultipleReplace(resource, replacement_dict)])
        return resources

    def GetRawResourceList(self, ResourceList):
        raw_resources = self.db.session.query(models.Resource.resource_name, models.Resource.resource).filter(
            models.Resource.resource_type.in_(ResourceList)).all()
        return raw_resources

    def GetResourceList(self, ResourceTypeList):
        replacement_dict = self.GetReplacementDict()
        raw_resources = self.GetRawResourceList(ResourceTypeList)
        resources = []
        for name, resource in raw_resources:
            resources.append([name, self.config.MultipleReplace(resource, replacement_dict)])
        return resources
