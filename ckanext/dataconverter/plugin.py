# encoding: utf-8

import ckan.plugins as p
import ckan.plugins.toolkit as tk

import sys, os
import uuid
import subprocess
#import docker

class DataconverterPlugin(p.SingletonPlugin, tk.DefaultDatasetForm):

    def __init__(self, name = None):
        self.config_path = None
    
    p.implements(p.IDatasetForm)
    p.implements(p.IConfigurer)
    p.implements(p.IResourceController, inherit=True)

    def after_create(self, context, resource):
        super(DataconverterPlugin, self).after_create(context, resource)
        # print(open("/home/mypc/Desktop/network_config.ini").read())
        # #tmp = DDSConector("/home/mypc/Desktop/file_idl.idl", "/home/mypc/Desktop/network_config.ini")
        # os.system(f"rm -rf /tmp/{self.uuid4}")
        # tmp.publish_example()
        print("$$$$$$$$$$$$$$$------after_create----$$$$$$$$$$$$$$$$$")
        print(context)
        print(resource)
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")

    def before_create(self, context, resource):
        print("*****************--------before_create------------********************")
        print(context)
        print(resource)
        if "network_config" in resource and "file_idl" in resource:
            uuid4 = uuid.uuid4().hex
            os.system(f"mkdir /tmp/{uuid4}")

            self.network_config = f"/tmp/{uuid4}/rtps.ini"
            resource["network_config"].save(self.network_config)
            del resource["network_config"]

            self.file_idl = f"/tmp/{uuid4}/Messenger.idl"
            resource["file_idl"].save(self.file_idl)
            del resource["file_idl"]

            result = subprocess.check_output(f"docker exec source_opendds-ckan_1 python3 ./source/run.py check -i {self.file_idl}", shell=True).decode()
            if result == "valid":
                os.system(f"docker exec -d source_opendds-ckan_1 python3 ./source/run.py run -t subscriber -i {self.file_idl} -n {self.network_config}")
            os.system(f"rm -rf /tmp/{uuid4}")
        print("*************************************")

    def before_update(self, context, current, resource):
        print("$$$$$$$$$$$$$$$------before_update----$$$$$$$$$$$$$$$$$")
        print(context)
        print(current)
        print(resource)
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")

    def update_config(self, config):
        # Add this plugin's templates dir to CKAN's extra_template_paths, so
        # that CKAN will use this plugin's custom templates.
        tk.add_template_directory(config, 'templates')

    # def create_package_schema(self):
    #     # let's grab the default schema in our plugin
    #     schema = super(DataconverterPlugin, self).create_package_schema()
    #     # our custom field
    #     schema.update({
    #         'cong_field1': [tk.get_validator('ignore_missing'),
    #                         tk.get_converter('convert_to_extras')]
    #     })
    #     return schema

    # def update_package_schema(self):
    #     schema = super(DataconverterPlugin, self).update_package_schema()
    #     # our custom field
    #     schema.update({
    #         'cong_field1': [tk.get_validator('ignore_missing'),
    #                         tk.get_converter('convert_to_extras')]
    #     })
    #     return schema



    def _modify_package_schema(self, schema):

        # Add our custom_test metadata field to the schema, this one will use
        # convert_to_extras instead of convert_to_tags.
        # schema.update({
        #         'cong_field1': [tk.get_validator('ignore_missing'),
        #             tk.get_converter('convert_to_extras')]
        #         })
        # # Add our custom_resource_text metadata field to the schema
        # schema['resources'].update({
        #         'file_idl' : [ tk.get_validator('ignore_missing') ]
        #         })
        # schema['resources'].update({
        #         'network_config' : [ tk.get_validator('ignore_missing') ]
        #     })
        return schema

    def create_package_schema(self):
        schema = super(DataconverterPlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(DataconverterPlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema


    def show_package_schema(self):
        schema = super(DataconverterPlugin, self).show_package_schema()
        # schema.update({
        #     'cong_field1': [tk.get_converter('convert_from_extras'),
        #                     tk.get_validator('ignore_missing')]
        # })

        # schema['resources'].update({
        #         'file_idl' : [ tk.get_validator('ignore_missing') ]
        #     })

        # schema['resources'].update({
        #         'network_config' : [ tk.get_validator('ignore_missing') ]
        #     })
        # print("^^^^^^^^^^^^^^^^^^^^^^^^")
        # print(schema)
        # print("^^^^^^^^^^^^^^^^^^^^^^^^")
        return schema

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []