import yaml

try:
    with open('_instances.yaml') as f:
        e2e_ip_dict = yaml.safe_load(f)
except FileNotFoundError:
    raise Exception('Please make sure the previous step has created the instances.yaml file')

e2e_ip_final = {'instances': {}}

for k, v in e2e_ip_dict.items():
    e2e_ip_final['instances'][f'{k}_HOST'] = v
    e2e_ip_final['instances'][f'{k}_PORT'] = 8000

with open('instances.yaml', 'w') as f:
    yaml.dump(e2e_ip_final, f)
