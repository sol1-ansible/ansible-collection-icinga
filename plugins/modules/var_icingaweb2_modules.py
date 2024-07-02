from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = '''
    name: var_icingaweb2_modules
'''
## Parse this
# icinga_shared_vars:
#   headends:
#     headend1:
#       name: icinga-ha-headend1.example.com
#       address: icinga-ha-headend1.example.com
#       api_user: root
#       api_password: API_USER_PASSWORD
#       redis_password: REPLACE_HEADEND1_REDIS_PASSWORD
#     headend2:
#       name: icinga-ha-headend2.example.com
#       address: icinga-ha-headend2.example.com
#       api_user: root
#       api_password: API_USER_PASSWORD
#       redis_password: REPLACE_HEADEND2_REDIS_PASSWORD
#   databases:
#     icingaweb:
#       dbname: icingaweb
#       host: localhost
#       password: CHANGE_ICINGAWEB_PASSWORD
#       resource_name: icingaweb_db
#     director:
#       dbname: director
#       host: localhost
#       password: CHANGE_DIRECTOR_PASSWORD
#       resource_name: director_db
#     icingadb:
#       dbname: icingadb
#       type: mysql
#       host: icingadb_db.example.com
#       password: CHANGE_ICINGADB_PASSWORD
#       resource_name: icingadb_db


## Into this
# icingaweb2_modules:
#   icingadb:
#     enabled: true
#     source: package
#     commandtransports:
#       "{{ icinga_shared_vars.headends.headend1.name }}":
#         transport: api
#         host: "{{ icinga_shared_vars.headends.headend1.address }}"
#         username: "{{ icinga_shared_vars.headends.headend1.api_user }}"
#         password: "{{ icinga_shared_vars.headends.headend1.api_password }}"
#       "{{ icinga_shared_vars.headends.headend2.name }}":
#         transport: api
#         host: "{{ icinga_shared_vars.headends.headend2.address }}"
#         username: "{{ icinga_shared_vars.headends.headend2.api_user }}"
#         password: "{{ icinga_shared_vars.headends.headend2.api_password }}"
#     config:
#       icingadb:
#         resource: "{{ icinga_shared_vars.databases.icingadb_web.resource_name }}"
#       redis:
#         tls: '0'
#     redis:
#       redis1:
#         host: "{{ icinga_shared_vars.headends.headend1.address }}"
#         port: 6380
#         password: "{{ icinga_shared_vars.headends.headend1.redis_password }}"
#       redis2:
#         host: "{{ icinga_shared_vars.headends.headend2.address }}"
#         port: 6380
#         password: "{{ icinga_shared_vars.headends.headend2.redis_password }}"
#   director:
#     enabled: true
#     source: package
#     import_schema: true
#     run_kickstart: true
#     kickstart:
#       config:
#         endpoint: "{{ icinga_shared_vars.headends.headend1.name }}"
#         host: "{{ icinga_shared_vars.headends.headend1.address }}"
#         username: "{{ icinga_shared_vars.headends.headend1.api_user }}"
#         password: "{{ icinga_shared_vars.headends.headend1.api_password }}"
#     config:
#       db:
#         resource: "{{ icinga_shared_vars.databases.director.resource_name }}"


# Function to build the icingaweb2_modules dictionary components
def build_icingadb_commandtransports(headends):
    commandtransports = {}
    for key, headend in headends.items():
        if isinstance(headend, dict) and key.startswith('headend'):
            commandtransports[headend['name']] = {
                'transport': 'api',
                'host': headend['address'],
                'username': headend['api_user'],
                'password': headend['api_password']
            }
    return commandtransports


def build_icingadb_config(headends, databases):
    config = {}
    if databases.get('icingadb', {}).get('resource_name', None) is not None:
        config['icingadb'] = {
            'resource': databases['icingadb']['resource_name']
        }
        config['redis'] = {
            'tls': '0'
        }
    return config


def build_icingadb_redis(headends):
    redis = {}
    for key, headend in headends.items():
        if isinstance(headend, dict) and str(key).startswith('headend'):
            # gets the headend number
            redis_key = f'redis{key[-1]}'
            redis[redis_key] = {
                'host': headend['address']
            }
            if headend.get('port', None) is not None:
                redis[redis_key]['port'] = headend['redis_port']
            else:
                redis[redis_key]['port'] = 6380
            if headend.get('redis_password', None) is not None:
                redis[redis_key]['redis_password'] = headend['redis_password']
    return redis

def build_icingadb_module(headends, databases):
    if 'icingadb' in databases:
        icingadb_module = {
            'enabled': True,
            'source': 'package',
            'commandtransports': build_icingadb_commandtransports(headends),
            'config': build_icingadb_config(headends, databases),
            'redis': build_icingadb_redis(headends)
        }
    return icingadb_module

def build_director_module(headends, databases):
    director = {}
    if 'director' in databases:
        director = {
            'enabled': True,
            'source': 'package',
            'run_kickstart': True,
            'kickstart': {
                'config': {
                    'endpoint': headends['headend1']['name'],
                    'host': headends['headend1']['address'],
                    'username': headends['headend1']['api_user'],
                    'password': headends['headend1']['api_password']
                }
            },
            'config': {
                'db': {
                    'resource': databases['director']['resource_name']
                }
            }
        }
        if databases.get('director', {}).get('import_schema', None) is not None:
            director['import_schema'] = True

    return director

def build_icingaweb2_modules(common_vars):
    icingaweb2_modules = {
        'icingadb': build_icingadb_module(common_vars['headends'], common_vars['databases']),
        'director': build_director_module(common_vars['headends'], common_vars['databases'])
    }
    return icingaweb2_modules

def main():
    module_args = dict(
        common_vars=dict(type='dict', required=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        built={}
    )

    common_vars = module.params['common_vars']

    built = build_icingaweb2_modules(common_vars)

    result['built'] = built
    module.exit_json(**result)

if __name__ == '__main__':
    main()
