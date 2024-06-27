from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = '''
    name: var_icinga2_features
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
#     zone: headend
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
#       host: icingadb_db.example.com
#       password: CHANGE_ICINGADB_PASSWORD
#       resource_name: icingadb_db


## Into this
# icinga2_features:
#   - name: api
#     force_newcert: false
#     ca_host: none
#     cert_name: "{{ inventory_hostname }}"
#     endpoints:
#       - name: "{{ icinga_shared_vars.headends.headend1.name }}"
#         host: "{{ icinga_shared_vars.headends.headend1.address }}"
#         port: "5665"
#       - name: "{{ icinga_shared_vars.headends.headend2.name }}"
#         host: "{{ icinga_shared_vars.headends.headend2.address }}"
#         port: "5665"
#     zones:
#       - name: headend
#         endpoints: 
#           - "{{ icinga_shared_vars.headends.headend1.name }}"
#           - "{{ icinga_shared_vars.headends.headend2.name }}"
#       - name: global
#         global: true
#       - name: director-global
#         global: true        
#   - name: checker
#   - name: command
#     state: present
#     command_path: /var/run/icinga2/cmd/icinga2.cmd
#   - name: notification
#   - name: mainlog    
#   - name: icingadb
#     host: localhost
#     password: "{{ icingadb_redis_password }}"
#     port: 6380   




# Function to build the icingaweb2_modules dictionary components
def build_icinga2_endpoints(endpoint_zones):
    _endpoints = []
    for endpoint_zone in endpoint_zones:
        for key, endpoint in endpoint_zone.items():
            if 'name' in endpoint:
                _endpoint = {
                    'name': endpoint['name']
                }
                if 'address' in endpoint:
                    _endpoint['host'] = endpoint
                    if 'port' in _endpoint:
                        _endpoint['port'] = endpoint['port']
                    else:
                        _endpoint['port'] = 5665
                _endpoints.append(_endpoint)
    return _endpoints

# Function to build a single zone, call this multiple times to build all zones
def build_icinga2_endpoint_zone(endpoints, zone):
    _endpoints = []
    for key, endpoint in endpoints.items():
        if 'name' in endpoint:
            _endpoints.append(endpoint['name'])
    zone = {
        'name': endpoints['zone'],
        'endpoints': _endpoints
    }
    return zone

# Function to build multiple global zones
def build_icinga2_global_zone(zones):
    _zone = []
    for zone in zones:
        _zone.append({
            'name': zone,
            'global': True
        })
    return _zone

def build_icinga2_zone(endpoint_zones = [], global_zones = []):
    zones = []
    for endpoint_zone in endpoint_zones:
        if 'zone' in endpoint_zone:
            zones.append(build_icinga2_endpoint_zone(endpoint_zone, endpoint_zone['zone']))
    zones.extend(build_icinga2_global_zone(global_zones))
    return zones

def build_icinga2_api(endpoint_zones, global_zones):
    api = {
        'name': 'api',
        'force_newcert': False,
        'ca_host': None,
        'endpoints': build_icinga2_endpoints(endpoint_zones),
        'zones': build_icinga2_zone(endpoint_zones, global_zones),
    }
    return api

def build_icinga2_notification(endpoints):
    notification = {
        'name': 'notification'
    }
    for key, endpoint in endpoints.items():
        # we are HA
        if str(key).endswith('2'):
            notification['enable_ha'] = True
    return notification

def build_icinga2_icingadb(icingadb):
    return {
        'name': 'icingadb',
        'host': 'localhost',
        'password': icingadb.get('password', 'MISSING - Fix me'),
        'port': icingadb.get('port', 6380)
    }
    


def build_icinga2_features(parent_endpoints, my_endpoints, config_directories, features):
    
    icinga2_features = [
        build_icinga2_api([parent_endpoints, my_endpoints], config_directories),
        {'name': 'checker'},
    ]
    if 'command' in features:
        icinga2_features.append({'name': 'command', 'state': 'present', 'command_path': '/var/run/icinga2/cmd/icinga2.cmd'})
    if 'notification' in features:
        icinga2_features.append(build_icinga2_notification(my_endpoints))
    if 'mainlog' in features:
        icinga2_features.append({'name': 'mainlog'})
    if 'icingadb' in features:
        icinga2_features.append(build_icinga2_icingadb(features['icingadb']))

    return icinga2_features

def main():
    module_args = dict(
        parent_endpoints=dict(type='dict', required=False, default={}),
        my_endpoints=dict(type='dict', required=True),
        config_directories=dict(type='list', required=True),
        features=dict(type='dict', required=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        merged={}
    )

    parent_endpoints = module.params['parent_endpoints']
    my_endpoints = module.params['my_endpoints']
    config_directories = module.params['config_directories']
    features = module.params['features']

    merged = build_icinga2_features(parent_endpoints, my_endpoints, config_directories, features)

    result['merged'] = merged
    module.exit_json(**result)

if __name__ == '__main__':
    main()