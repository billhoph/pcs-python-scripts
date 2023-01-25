""" Get Resources """

# pylint: disable=import-error
from prismacloud.api import pc_api, pc_utility
from datetime import date
from tabulate import tabulate
import time
import shutil
import os
import pandas as pd

# --Configuration-- #

parser = pc_utility.get_arg_parser()
parser.add_argument(
    'severity',
    type=str,
    default='high',
    help='Alert Serverity Level, Default=High')
#parser.add_argument(
#    'status',
#    type=str,
#    default='open',
#    help='Alert Status, Default = Open')
parser.add_argument(
    'type',
    type=str,
    default='config',
    help='Policy Type, Default = Config')
args = parser.parse_args()

# --Initialize-- #

pc_utility.prompt_for_verification_to_continue(args)
settings = pc_utility.get_settings(args)
pc_api.configure(settings)

# --Main-- #

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
        {"name":"policy.severity", "operator":"=", "value": "%s" % args.severity},
        {"name":"policy.type","operator":"=", "value": "%s" % args.type}
    ],
    "groupBy": [
        "cloud.account"
    ],
    "limit": 1000,
    "offset": 0,
    "sortBy": [
        "cloud.account"
    ],
    "timeRange": {
      "relativeTimeType": "BACKWARD",
      "type": "relative",
      "value": {
        "amount": 7,
        "unit": "day"
        }
    }
}

print(body_params)

print()
print('Creating the Alert Report...', end='')
print()
alert_report = pc_api.alert_csv_create(body_params)
print('Report Created with Report ID: %s' % alert_report['id'])
report_time = time.strftime("%Y%m%d-%H%M%S")
report_filename = "./Report-Current/wistron-report-" + report_time + ".csv"
print()

report_ready = False
current_report_dir = './Report-Current'
last_report_dir = './Report-Last'
repo_report_dir = './Report-Repo'
info_report_dir = './Report-Info'
output_report_dir = './Report-Output'
info_csv_path = info_report_dir + '/' + 'wistron-info.csv'

while(not report_ready):
    alert_report_update = pc_api.alert_csv_status(alert_report['id'])
    print('Getting the Alert Report Status...', alert_report_update['status'])
    time.sleep(2.5)    
    if (alert_report_update['status'] == 'READY_TO_DOWNLOAD'):
        csv_report = pc_api.alert_csv_download(alert_report['id'])
        file_names = os.listdir(current_report_dir)

        # Move Files Generate previously to Repo
        for file_name in file_names:
            shutil.move(os.path.join(current_report_dir, file_name), os.path.join(repo_report_dir, file_name))

        # Write Download Report File to Current Report Directory
        file = open(report_filename, "w")
        file.write(csv_report)
        file.close()
        print("Alert Report Downloaded...")
        file_names = os.listdir(last_report_dir)

        if len(file_names) != 0:
            # Compare Previous and New Report File to info Folder
            data1 = pd.read_csv(report_filename)
            for file_name in file_names:
                data2 = pd.read_csv(last_report_dir + '/' + file_name)
            #merged_data = pd.concat([data1,data2]).drop_duplicates(keep=False)
            merged_data = pd.concat([data2,data1])
            diff_data = merged_data.groupby('Alert ID')['Alert Status'].apply('>'.join).reset_index()
            diff_df = pd.DataFrame(diff_data)
            diff_df.rename(columns={'Alert Status' : 'Alert Status Change'})
            diff_csv = 'wistron-alert-updates-' + report_time + '.csv'
            diff_df.to_csv(info_report_dir + '/' + diff_csv,index=None)
            print("Comparing with last report...")

        # Move Files Generate previously to Repo
        for file_name in file_names:
            shutil.move(os.path.join(last_report_dir, file_name), os.path.join(repo_report_dir, file_name))

        print("Generating report with Wistron Information...")
        report_csv = data2
        report_csv.head()

        info_csv = pd.read_csv(info_csv_path)
        info_csv.head()

        if len(file_names) != 0:
            alert_status_csv = pd.read_csv(info_report_dir + '/' + diff_csv)
            alert_status_csv.head()
            inner_join_1 = pd.merge(report_csv, 
                      info_csv, 
                      on ='Cloud Account Id', 
                      how ='left')
            inner_join_2 = pd.merge(inner_join_1, 
                      alert_status_csv, 
                      on ='Alert ID', 
                      how ='left')
            df = pd.DataFrame(inner_join_2)
        else:
            inner_join_1 = pd.merge(report_csv, 
                      info_csv, 
                      on ='Cloud Account Id', 
                      how ='left')
            df = pd.DataFrame(inner_join_1)
            df.insert(24,'Alert Status Change',"")

        df.insert(25,'Service Description',"")
        df.insert(26,"Status \n(C = Completed\nO = Open)","")

        # exporting to Excel
        output_filename = output_report_dir + '/wistron-merged-report-' + report_time + '.xlsx'
        df.to_excel(output_filename,index = False, header=True)

        print("Report Generation Completed...")

        file_names = os.listdir(current_report_dir)
        for file_name in file_names:
            shutil.move(os.path.join(current_report_dir, file_name), last_report_dir)
        break