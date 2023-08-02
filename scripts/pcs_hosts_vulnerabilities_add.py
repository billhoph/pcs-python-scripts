""" Get Vulnerabilities in Hosts (Running Hosts) """

import json
import csv


# pylint: disable=import-error
from prismacloud.api import pc_api, pc_utility

# --Configuration-- #

parser = pc_utility.get_arg_parser()
args = parser.parse_args()

# --Helpers-- #

def optional_print(txt='', mode=True):
    if mode:
        print(txt)

# --Initialize-- #

settings = pc_utility.get_settings(args)
pc_api.configure(settings)
pc_api.validate_api_compute()

# --Main-- #

print('Testing Compute API Access ...', end='')
intelligence = pc_api.statuses_intelligence()
print(' done.')
print()

with open('./Vul/vul_baseline.csv', newline='') as csvfile:
    rows = csv.reader(csvfile)
    for row in rows:
        body_params = {
            "id": row[0],
            "packageName": "*",
            "resourceType": "host",
            "resources": [
                "ip-*"
            ]
        }
        print(body_params)

