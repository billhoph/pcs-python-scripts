""" Get Resources """

# pylint: disable=import-error
from prismacloud.api import pc_api, pc_utility
import pandas as pd
import time
import datetime
import json

# --Configuration-- #

parser = pc_utility.get_arg_parser()
parser.add_argument(
    'week',
    type=int,
    help="number of week before today")
args = parser.parse_args()

# --Initialize-- #

# pc_utility.prompt_for_verification_to_continue(args)
settings = pc_utility.get_settings(args)
pc_api.configure(settings)

dt = datetime.datetime(year=2022, month=1, day=1)
start_ts = time.mktime(dt.timetuple())*1000
weeks = args.week

for x in range(weeks):
    end_ts = time.mktime((datetime.datetime.today() - datetime.timedelta(weeks)).timetuple())*1000
    print('API - Gernerate new CSV Report ...', end='')
    body_params = {
        "detailed": True,
        "fields":[
            "alert.id",
            "alert.status",
            "alert.time",
            "cloud.account",
            "cloud.accountId",
            "cloud.region",
            "resource.id",
            "resource.name",
            "policy.name",
            "policy.type",
            "policy.severity"
        ],
        "filters":[
            {"name":"policy.severity", "operator":"=", "value": "high"},
            {"name":"policy.severity", "operator":"=", "value": "critical"},
            {"name":"policy.severity", "operator":"=", "value": "medium"},
            {"name":"alert.status","operator":"=", "value": "open"}
        ],
        "groupBy": [
            "cloud.account"
        ],
        "limit": 2000,
        "offset": 0,
        "sortBy": [
            "cloud.account"
        ],
        "timeRange": {
        "type": "absolute",
        "value": {
            "startTime": start_ts,
            "endTime": end_ts
            }
        }
    }

    print()
    print('Creating the Alert Report...', end='')
    print()
    alert_report = pc_api.alert_csv_create(body_params)
    print('Report Created with Report ID: %s' % alert_report['id'])
    report_time = time.strftime("%Y%m%d-%H%M%S")
    report_filename = "./Reports/customer-report-" + report_time + "-" + weeks + ".csv"
    print()

    report_ready = False
    report_dir = './Reports'

    while(not report_ready):
        alert_report_update = pc_api.alert_csv_status(alert_report['id'])
        print('Getting the Alert Report Status...', alert_report_update['status'])
        time.sleep(2.5)    
        if (alert_report_update['status'] == 'READY_TO_DOWNLOAD'):
            csv_report = pc_api.alert_csv_download(alert_report['id'])

            # Write Download Report File to Current Report Directory
            file = open(report_filename, "w")
            file.write(csv_report)
            file.close()
            print("Alert Report Downloaded...")
            break
