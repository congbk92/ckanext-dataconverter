# encoding: utf-8

import ckan.plugins as p
import ckan.plugins.toolkit as tk

import sys, os
import uuid
import subprocess
#import docker
import configparser
from werkzeug.datastructures import FileStorage
import re

class DataconverterPlugin(p.SingletonPlugin, tk.DefaultDatasetForm):

    def __init__(self, name = None):
        self.config_path = None
        self.config = configparser.ConfigParser()
        self.common_config = {'ckan_sever' : 'http://localhost:5000'}
        self.uuid4 = uuid.uuid4().hex
        self.env = dict()

    p.implements(p.IDatasetForm)
    p.implements(p.IConfigurer)
    p.implements(p.IResourceController, inherit=True)
    p.implements(p.IValidators)

    def after_create(self, context, resource):
        self.config_path = f'/tmp/{self.uuid4}/config.ini'
        super(DataconverterPlugin, self).after_create(context, resource)
        print("$$$$$$$$$$$$$$$------after_create----$$$$$$$$$$$$$$$$$")
        print(context)
        print(resource)
        if "source_type" in resource and resource["source_type"] == "dds_static":
            result = subprocess.check_output(f"docker exec source_opendds-ckan_1 python3 ./source/run.py check -i {self.env['file_idl']}", shell=True).decode()
            if result.strip() == "valid":
                self.common_config['resource_id'] = resource["id"]
                self.common_config['package_id'] = resource["package_id"]
                self.common_config['name'] = resource["name"] if resource["name"] else self.uuid4

                self.config['common'] = self.common_config
                self.config['dds'] =  { "mode" : "subscriber",
                                        "topic_name" : resource["topic_name"],
                                        "file_idl" : self.env["file_idl"],
                                        "network_config" : self.env["network_config"]}
                    
                with open(f'{self.config_path}', 'w') as configfile:
                    self.config.write(configfile)
                os.system(f"docker exec -d source_opendds-ckan_1 python3 ./source/run.py run -c {self.config_path}")
        #To Do:
        #os.system(f"rm -rf /tmp/{self.uuid4}")
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")

    def before_create(self, context, resource):
        self.uuid4 = uuid.uuid4().hex
        print("*****************--------before_create------------********************")
        print(context)
        print(resource)
        self.common_config['api_token'] = context["auth_user_obj"].apikey
        os.system(f"mkdir /tmp/{self.uuid4}")

        if "network_config" in resource and "file_idl" in resource:
            #network_config_validator(resource["network_config"])
            #file_idl_validator(resource["file_idl"])

            network_config_path = f"/tmp/{self.uuid4}/rtps.ini"
            resource["network_config"].save(network_config_path)
            del resource["network_config"]

            file_idl_path = f"/tmp/{self.uuid4}/Messenger.idl"
            print(file_idl_path)
            resource["file_idl"].save(file_idl_path)
            del resource["file_idl"]

            self.env["network_config"] = network_config_path
            self.env["file_idl"] = file_idl_path
            self.common_config['converter'] = 'dds'


        if not resource["name"] and "topic_name" in resource:
            resource["name"] = resource["topic_name"]
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
        #         'cong_field1': [tk.get_validator('not_missing'),
        #             tk.get_converter('convert_to_extras')]
        #         })
        # # Add our custom_resource_text metadata field to the schema
        schema['resources'].update({
                'file_idl' : [ tk.get_validator('ignore_missing'),
                                tk.get_converter('convert_to_extras')]
                })
        schema['resources'].update({
                'network_config' : [ tk.get_validator('ignore_missing'),
                                        tk.get_converter('convert_to_extras')]
            })
        schema['resources'].update({
                'topic_name' : [ tk.get_validator('topic_name_validator'),
                                    tk.get_converter('convert_to_extras')]
            })
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
        
        schema['resources'].update({
                'file_idl' : [ tk.get_validator('ignore_missing'),
                                tk.get_converter('convert_to_extras')]
                })
        schema['resources'].update({
                'network_config' : [ tk.get_validator('ignore_missing'),
                                        tk.get_converter('convert_to_extras')]
            })
        schema['resources'].update({
                'topic_name' : [ tk.get_validator('topic_name_validator'),
                                    tk.get_converter('convert_to_extras')]
            })
        print("^^^^^^^^^^^^^^^^^^^^^^^^")
        print(schema)
        print("^^^^^^^^^^^^^^^^^^^^^^^^")
        return schema

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    # def validate(self, context, data_dict, schema, action):
    #     file_idl = data_dict.get("file_idl")
    #     network_config = data_dict.get("network_config")
    #     topic_name = data_dict.get("topic_name")
    #     err_dict = dict()
    #     if file_idl is not None and type(file_idl) is not FileStorage:
    #         err_dict["file_idl"] = ["IDL file is missing"]
    #     if network_config is not None and type(network_config) is not FileStorage:
    #         err_dict["network_config"] = ["Network config file is missing"]
    #     if topic_name == "":
    #         err_dict["topic_name"] = ["Topic name is missing"]

    #     result = super(DataconverterPlugin, self).validate(context, data_dict, schema, action)
    #     print("type", type(result))
    #     print("validate", result)
    #     #return (data_dict, err_dict)
    #     return result

    def get_validators(self):
        return {
            u'file_idl_validator': file_idl_validator,
            u'network_config_validator': network_config_validator,
            u'topic_name_validator': topic_name_validator,
        }


def file_idl_validator(key, data, errors, context):
    value = data.get(key)
    print("#################file_idl_validator#################")
    print(data)
    print(type(value))
    print(errors)
    print("@@@@@@@@@@@@@@@@@file_idl_validator@@@@@@@@@@@@@@@@@")
    if value is not None and type(value) is not FileStorage:
        raise tk.Invalid(u"IDL file isn't uploaded")
    elif type(value) is FileStorage:
        tmp_uuid = uuid.uuid4().hex
        os.system(f"mkdir /tmp/{tmp_uuid}")
        tmp_idl_file = f"/tmp/{tmp_uuid}/Messenger.idl"
        value.save(tmp_idl_file)
        command = f"docker exec source_opendds-ckan_1 python3 ./source/run.py check -i {tmp_idl_file}"
        result = subprocess.check_output(command, shell=True).decode()
        if result.strip() != "valid":
            raise tk.Invalid(u"IDL file is invalid. Please check!")
    return value

def network_config_validator(key, data, errors, context):
    value = data.get(key)
    if value is not None and type(value) is not FileStorage:
        raise tk.Invalid(u"Network config file isn't uploaded")
    elif type(value) is FileStorage:
        tmp_uuid = uuid.uuid4().hex
        os.system(f"mkdir /tmp/{tmp_uuid}")
        tmp_ini_file = f"/tmp/{tmp_uuid}/rtps.ini"
        value.save(tmp_ini_file)
        try:
            config = configparser.ConfigParser()
            config.read_file(open(tmp_ini_file))
        except configparser.Error:
            raise tk.Invalid(u"Network config file is invalid. Please check!")
    return value

def topic_name_validator(value):
    if value == "":
        raise tk.Invalid(u"Topic name is missing")
    elif type(value) is str:
        x = re.match(r'[_a-zA-z][_a-zA-z0-9]*', value)
        if x is None:
            raise tk.Invalid(u"Topic name is invalid. Please check!")
    return value