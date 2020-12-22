# encoding: utf-8

import ckan.plugins as p
import ckan.plugins.toolkit as tk

import sys, os
import uuid
import subprocess
#import docker
import configparser

class DataconverterPlugin(p.SingletonPlugin, tk.DefaultDatasetForm):

    def __init__(self, name = None):
        self.config_path = None
        self.config = configparser.ConfigParser()
        self.common_config = {   'ckan_sever' : 'http://localhost:5000',
                                    'mongodb_sever' : 'http://localhost:27017'}
        self.uuid4 = uuid.uuid4().hex
        self.config_path = f'/tmp/{self.uuid4}/config.ini'
        self.env = dict()

    p.implements(p.IDatasetForm)
    p.implements(p.IConfigurer)
    p.implements(p.IResourceController, inherit=True)

    def after_create(self, context, resource):
        super(DataconverterPlugin, self).after_create(context, resource)
        print("$$$$$$$$$$$$$$$------after_create----$$$$$$$$$$$$$$$$$")
        print(context)
        print(resource)
        if resource["source_type"] == "dds_static":
            result = subprocess.check_output(f"docker exec source_opendds-ckan_1 python3 ./source/run.py check -i {self.env['file_idl']}", shell=True).decode()
            if result.strip() == "valid":
                self.common_config['resource_id'] = resource["id"]
                self.config['common'] = self.common_config
                self.config['dds'] =  { "mode" : "subscriber",
                                        "topic_name" : resource["topic_name"],
                                        "file_idl" : self.env["file_idl"],
                                        "network_config" : self.env["network_config"]}
                    
                with open(f'{self.config_path}', 'w') as configfile:
                    self.config.write(configfile)
                os.system(f"docker exec -d source_opendds-ckan_1 python3 ./source/run.py -f {self.config_path}")

        #To Do:
        #os.system(f"rm -rf /tmp/{self.uuid4}")
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")

    def before_create(self, context, resource):
        print("*****************--------before_create------------********************")
        print(context)
        print(resource)
        self.common_config['api_token'] = context["auth_user_obj"].apikey
        os.system(f"mkdir /tmp/{self.uuid4}")

        if "network_config" in resource and "file_idl" in resource:
            network_config_path = f"/tmp/{self.uuid4}/rtps.ini"
            resource["network_config"].save(network_config_path)
            del resource["network_config"]

            file_idl_path = f"/tmp/{self.uuid4}/Messenger.idl"
            resource["file_idl"].save(file_idl_path)
            del resource["file_idl"]

            self.env["network_config"] = network_config_path
            self.env["file_idl"] = file_idl_path
        print("*************************************")
        super(DataconverterPlugin, self).before_create(context, resource)

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