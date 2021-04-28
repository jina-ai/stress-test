import sys
import time
import json
import requests

if len(sys.argv) < 2:
    raise Exception('IPs are not passed')

total_time_to_wait = 120
init_time = time.time()
check_until = init_time + total_time_to_wait

e2e_ip_dict = json.loads(sys.argv[1].strip("\"").replace('\\', ''))
e2e_ip_validate = {}

while time.time() < check_until and sum(e2e_ip_validate.values()) != len(e2e_ip_dict):
    for jinad_ip in e2e_ip_dict.values():
        try:
            e2e_ip_validate[jinad_ip] = True \
                if requests.get(f'http://{jinad_ip}:8000').status_code == requests.codes.ok \
                else False
        except requests.ConnectionError:
            e2e_ip_validate[jinad_ip] = False
    print(f'Current status: {e2e_ip_validate}')


if time.time() > check_until:
    print(f'Tried to connect to all jinad instances for {total_time_to_wait} secs, timing out now.')
    sys.exit(1)
else:
    print(f'Hurray! Successfully connected to all JinaD instances. Took ~{time.time() - init_time:.0f} secs')
