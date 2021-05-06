import sys
import time
import requests

import yaml

try:
    with open('_instances.yaml') as f:
        e2e_ip_dict = yaml.safe_load(f)
except FileNotFoundError:
    raise Exception('Please make sure the previous step has created the instances.yaml file')

total_time_to_wait = 120
init_time = time.time()
check_until = init_time + total_time_to_wait
e2e_ip_validate = {}

for instance_name in e2e_ip_dict.copy().keys():
    if 'client' in instance_name.lower():
        e2e_ip_dict.pop(instance_name)


while time.time() < check_until and sum(e2e_ip_validate.values()) != len(e2e_ip_dict):
    for instance_name, ip in e2e_ip_dict.items():
        try:
            e2e_ip_validate[ip] = True \
                if requests.get(f'http://{ip}:8000', timeout=5).status_code == requests.codes.ok \
                else False
        except requests.ConnectionError:
            print(f'Timeout for {instance_name}:{ip}')
            e2e_ip_validate[ip] = False
    print(f'Current status: {e2e_ip_validate}, sleeping for a second!')
    time.sleep(1)


if time.time() > check_until:
    print(f'Tried to connect to all jinad instances for {total_time_to_wait} secs, timing out now.')
    sys.exit(1)
else:
    print(f'Hurray! Successfully connected to all JinaD instances. Took ~{time.time() - init_time:.0f} secs')
