import sys
import json
import yaml

if len(sys.argv) < 2:
    raise Exception('IPs are not passed')

e2e_ip_dict = json.loads(sys.argv[1].strip("\"").replace('\\', ''))
e2e_ip_final = {'instances': {}}

for k, v in e2e_ip_dict.items():
    e2e_ip_final['instances'][f'{k}_HOST'] = v
    e2e_ip_final['instances'][f'{k}_PORT'] = 8000

with open('instances.yaml', 'w') as f:
    yaml.dump(e2e_ip_final, f)
