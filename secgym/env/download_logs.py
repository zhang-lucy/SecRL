import os
import pandas as pd
import json
from datetime import timedelta, datetime, timezone
from azure.monitor.query import LogsQueryClient, LogsQueryStatus
from azure.core.exceptions import HttpResponseError
from azure.identity import DefaultAzureCredential
from utils import to_abs_path

credential = DefaultAzureCredential()
client = LogsQueryClient(credential)

def query_data(query, start_time, duration):
    response = client.query_workspace("0fbd2874-9307-4572-b499-f8fa3cc75daf", query, timespan=(start_time, duration))
    if response.status == LogsQueryStatus.SUCCESS:
        return response.tables
    else:
        return response.partial_data

def query_and_save_data(table_name, start_time, duration, file_path, post_fix=""):
    os.makedirs(file_path, exist_ok=True)

    query = table_name.split("_")[0]
    print(f"Querying table {query}...")
    data = query_data(query, start_time, duration)
    if data is None:
        print(f"{table_name} is None. Skipping.")
        return

    for table in data:
        df = pd.DataFrame(data=table.rows, columns=table.columns)
        if len(df) == 0:
            print(f"Table {table_name} is empty. Skipping.")
            return
        metadata = dict(zip(df.columns.tolist(), table.columns_types))

        json_columns = [col for col, dtype in metadata.items() if dtype == "dynamic"]
        for column in json_columns:
            df[column] = df[column].apply(lambda x: "{}" if x == "" else x)
            df[column] = df[column].apply(lambda x: "{}" if pd.isnull(x) else x)

        df.to_csv(
            os.path.join(file_path, f"{table_name}{post_fix}.csv"), 
            index=False, 
            sep="¤",
            encoding='utf-8'
            ) # Note: sep="|" is used
        
        with open(os.path.join(file_path, f"{table_name}.meta"), 'w') as f:
            json.dump(metadata, f, indent=4)        
        print(f"Table {table_name} saved successfully with {len(df)} rows.")



LIST_TABLES = [
    "AADManagedIdentitySignInLogs",
    "AADNonInteractiveUserSignInLogs",
    "AADRiskyUsers",
    "AADServicePrincipalSignInLogs",
    "AADUserRiskEvents",
    "AuditLogs",
    "AzureActivity",
    "Heartbeat",
    "MicrosoftGraphActivityLogs",
    "Operation",
    "SigninLogs",
    "Usage",

    "AlertEvidence",
    "AlertInfo",
    "CloudAppEvents",
    "DeviceEvents",
    "DeviceFileCertificateInfo",
    "DeviceFileEvents",
    "DeviceImageLoadEvents",
    "DeviceInfo",
    "DeviceLogonEvents",
    "DeviceNetworkEvents",
    "DeviceNetworkInfo",
    "DeviceProcessEvents",
    "DeviceRegistryEvents",
    "EmailEvents",
    "EmailUrlInfo",
    "IdentityDirectoryEvents",
    "IdentityLogonEvents",
    "IdentityQueryEvents",
    "OfficeActivity",
    "SecurityAlert",
    # "SecurityEvent", # large data need further processing
    "SecurityIncident",
    "Watchlist",
    "WindowsEvent",
    "ThreatIntelligenceIndicator",

    # "SecurityAlert",
    # "SecurityEvent",
]


if __name__ == "__main__":

    file_path = to_abs_path("data/addcomp_jul25")
    start_time = datetime(2024, 7, 25, 15, 0, 0, 0, tzinfo=timezone.utc)

    # for 3 hours
    duration = timedelta(hours=3)
    end_time = start_time + duration

    # start_time = datetime(2024, 6, 26, 23, 59, 59, 999999, tzinfo=timezone.utc)
    # end_time = datetime(2024, 7, 3, 23, 59, 59, 999999, tzinfo=timezone.utc)

    for table_name in LIST_TABLES:
        # if table_name != "AADManagedIdentitySignInLogs":
        #     continue
        if os.path.exists(os.path.join(file_path, f"{table_name}.csv")):
            print(f"Table {table_name} already exists. Skipping.")
            continue
        
        try:
            query_and_save_data(table_name, start_time, duration, file_path)
        except HttpResponseError as e:
            print(f"Error querying table {table_name}.")
            file_path = os.path.join(file_path, table_name)
            os.makedirs(os.path.join(file_path, table_name), exist_ok=True)

            # save data per day
            if end_time - start_time > timedelta(days=1):
                # iterate from start_time to end_time day by day
                # and save the data for each day
                current_time = start_time
                post_fix = 0
                while current_time < end_time:
                    next_time = current_time + timedelta(days=1)
                    if next_time > end_time:
                        next_time = end_time
                    try:
                        query_and_save_data(table_name, current_time, next_time, os.path.join(file_path, table_name), "_" + str(post_fix))
                    except Exception as e:
                        print(f"Error querying table {table_name} from {current_time} to {next_time}.")
                    current_time = next_time   
                    post_fix += 1
            else:
                raise e
                

        




