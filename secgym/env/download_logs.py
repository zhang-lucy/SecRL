import os
import pandas as pd
import json
from datetime import timedelta, datetime, timezone
from azure.monitor.query import LogsQueryClient, LogsQueryStatus
from azure.core.exceptions import HttpResponseError
from azure.identity import DefaultAzureCredential
from typing import Optional, Union, Tuple
from textwrap import dedent

credential = DefaultAzureCredential()
client = LogsQueryClient(credential)

def get_count(
        workspace_id: str,
        table_name: str,
        timpespan: Optional[Union[timedelta, Tuple[datetime, timedelta], Tuple[datetime, datetime]]]
    ) -> int:

    response = client.query_workspace(workspace_id, f"{table_name} | count", timespan=timpespan)

    if response.status == LogsQueryStatus.SUCCESS:
        return response.tables[0].rows[0][0]
    else:
        return -1
    
def calculate_size_per_entry(
        workspace_id: str,
        table_name: str,
        timpespan: Optional[Union[timedelta, Tuple[datetime, timedelta], Tuple[datetime, datetime]]]
    ) -> int:

    response = client.query_workspace(workspace_id, f"{table_name} | limit 2000", timespan=timpespan, include_statistics=True)
    if response.status == LogsQueryStatus.SUCCESS:
        if  response.statistics['query']['datasetStatistics'][0]['tableRowCount'] == 0:
            print(f"Table {table_name} is empty.")
            return 0
        return response.statistics['query']['datasetStatistics'][0]['tableSize'] / response.statistics['query']['datasetStatistics'][0]['tableRowCount']
    else:
        return -1
    

def check_segemented_query(
        workspace_id: str,
        table_name: str,
        timespan: Optional[Union[timedelta, Tuple[datetime, timedelta], Tuple[datetime, datetime]]],
        max_size_allowed: int = 60000000, # in bytes, ~60MB
        max_count_allowed: int = 500000,
        verbose: bool = False
    ) -> Tuple[bool, int]:
    """
    Check if the query need to be segmented or not
    
    Args:
    - workspace_id: Azure Log Analytics workspace id
    - table_name: table name to query
    - timespan: time range to query
    - max_size_allowed: maximum size allowed for a single query
    - max_count_allowed: maximum count allowed for a single query

    Returns:
    - Tuple[bool, int, int, int]:
        - bool: if the query need to be segmented or not
        - int: number of row per query
        - int: total count of the table
        - int: total size of the table, in bytes
    """
    # https://learn.microsoft.com/en-us/azure/azure-monitor/service-limits#la-query-api

    total_count = get_count(workspace_id, table_name, timespan)
    size_per_entry = calculate_size_per_entry(workspace_id, table_name, timespan)
    if total_count == -1 or size_per_entry == -1:
        return True, 0, -1, -1
    total_size = total_count * size_per_entry 
    if total_size < max_size_allowed and total_count < max_count_allowed:
        if verbose:
            print(f"Total count: {total_count}", f"Size per entry: {size_per_entry}", f"Total size: {total_size/1024/1024} MB")
        return False, -1, total_count, total_size
    
    row_per_query = max_count_allowed
    if total_size > max_size_allowed:
        # get number of row per query 
        row_per_query = min(row_per_query, max_size_allowed // size_per_entry)
    
    if verbose:
        print(f"Table: {table_name}", 
              f"Total count: {total_count}", 
              f"Size per entry: {size_per_entry} Bytes", 
              f"Total size: {total_size/1024/1024} MB", 
              f"Row per query: {row_per_query}", 
              f"Estimate table count: {total_count // row_per_query}",
              sep=", ",
              )
    return True, int(row_per_query), total_count, total_size

def save_table(file_path_name, response, need_metadata=False):
    """Helper function of `query_and_save_data` to save the table to a csv file"""
    table = response.tables[0]
    df = pd.DataFrame(data=table.rows, columns=table.columns)
    if len(df) == 0:
        return -1, -1
    metadata = dict(zip(df.columns.tolist(), table.columns_types))
    if need_metadata:
        with open(file_path_name.replace(".csv", ".meta"), "w") as f:
            json.dump(metadata, f)

    json_columns = [col for col, dtype in metadata.items() if dtype == "dynamic"]
    for column in json_columns:
        df[column] = df[column].apply(lambda x: "{}" if x == "" else x)
        df[column] = df[column].apply(lambda x: "{}" if pd.isnull(x) else x)
    
    df.to_csv(file_path_name, index=False, sep="¤", encoding='utf-8')
    return df["TimeGenerated"].min(), df["TimeGenerated"].max()

def query_and_save_data(
        workspace_id: str,
        table_name: str,
        timespan: Optional[Union[timedelta, Tuple[datetime, timedelta], Tuple[datetime, datetime]]],
        file_path: str,
        verbose: bool = False
):
    
    max_size_allowed: int = 60000000
    need_segement, row_per_query, total_count, total_size = check_segemented_query(workspace_id, table_name, timespan, verbose=verbose, max_size_allowed=max_size_allowed)

    if need_segement:
        updated_file_path = os.path.join(file_path, table_name)
        os.makedirs(updated_file_path, exist_ok=True)
        
        # get total time range in hours, conver to start and end time
        if isinstance(timespan, timedelta):
            timespan = (datetime.utcnow() - timespan, datetime.utcnow())
        elif isinstance(timespan[1], timedelta):
            total_hours = timespan[1].total_seconds() / 3600
            timespan = (timespan[0], timespan[0] + timespan[1])
        else:
            total_hours = (timespan[1] - timespan[0]).total_seconds() / 3600
        
        # print(type(timespan[0]))
        # get size per hour
        size_per_hour = total_size / total_hours
        # approximate 200MB per time chunk
        time_chunk = int(200 * 1024 * 1024 / size_per_hour)
        print(f"Time chunk: {time_chunk} hours")

        tmp_start_time = timespan[0]
        chunk_id = 0
        # if table_name == "AADNonInteractiveUserSignInLogs":
        #     # 2024-07-15 13:02:04.923788+00:00
        #     tmp_start_time = datetime(2024, 7, 15, 13, 2, 4, 923788, tzinfo=timezone.utc) + timedelta(milliseconds=1)
        #     chunk_id = 44
        #     print(f"Resuming from chunk 44, {tmp_start_time}")
        query_template = dedent("""{table_name} 
| order by TimeGenerated asc
| serialize
| extend rn = row_number() 
| where rn <= {end}
""")        
        while tmp_start_time < timespan[1]:
            # get data from a time chunk
            tmp_timespan = (tmp_start_time, min(tmp_start_time + timedelta(hours=time_chunk), timespan[1]))

            response = client.query_workspace(
                workspace_id, 
                query_template.format(table_name=table_name, end=row_per_query),
                timespan=tmp_timespan
            ) # only return the first row_per_query rows
    
            if response.status != LogsQueryStatus.SUCCESS:
                error = response.partial_error
                print(f"Getting error, retry chunk {chunk_id}", error)
                # update max size allowed and row per query
                max_size_allowed -= 2000000
                row_per_query = min(row_per_query, max_size_allowed // (total_size/total_count))
            else:
                # set new start time to be the last time from the response
                earliest, latest = save_table(os.path.join(updated_file_path, f"{table_name}_{chunk_id}.csv"), response, need_metadata=chunk_id == 0)
                if earliest == -1:
                    print(f"Reached end of the table. Exiting.")
                    break
                # from pd timestamp to datetime.datetime, and +1 in milliseconds
                tmp_start_time = latest.to_pydatetime() + timedelta(milliseconds=1)
                chunk_id += 1
                print(f"Chunk {chunk_id}: {earliest} - {latest}")  #Required span: {tmp_timespan} || Actual:
            
    else:
        response = client.query_workspace(workspace_id, f"{table_name}", timespan=timespan)
        earliest, _ = save_table(os.path.join(file_path, f"{table_name}.csv"), response, need_metadata=True)
        if earliest == -1:
            print(f"Table {table_name} is empty. Skipping.")
        else:
            print(f"Table {table_name} is saved.")

LIST_TABLES = [
    "AADManagedIdentitySignInLogs",
    "AADNonInteractiveUserSignInLogs",
    "AADProvisioningLogs",
    "AADRiskyUsers",
    "AADServicePrincipalSignInLogs",
    "AADUserRiskEvents",
    "Alert",
    "AmlDataLabelEvent",
    "AmlDataStoreEvent",
    "AuditLogs",
    "AZFWApplicationRule",
    "AZFWApplicationRuleAggregation",
    "AZFWDnsQuery",
    "AZFWFlowTrace",
    "AZFWIdpsSignature",
    "AZFWNatRule",
    "AZFWNatRuleAggregation",
    "AZFWNetworkRule",
    "AZFWNetworkRuleAggregation",
    "AZFWThreatIntel",
    "AzureActivity",
    # "AzureDiagnostics",
    "AzureMetrics",
    "ContainerRegistryRepositoryEvents",
    "Heartbeat",
    "IntuneAuditLogs",
    "IntuneDeviceComplianceOrg",
    "IntuneDevices",
    "IntuneOperationalLogs",
    "LAQueryLogs",
    "LASummaryLogs",
    "MicrosoftAzureBastionAuditLogs",
    "MicrosoftGraphActivityLogs",
    "NetworkAccessTraffic",
    "Operation",
    "SigninLogs",
    "Usage",
    "Windows365AuditLogs",

    "AlertEvidence",
    "AlertInfo",
    "Anomalies",
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
    "EmailAttachmentInfo",
    "EmailEvents",
    "EmailPostDeliveryEvents",
    "EmailUrlInfo",
    "HuntingBookmark",
    "IdentityDirectoryEvents",
    "IdentityLogonEvents",
    "IdentityQueryEvents",
    "OfficeActivity",
    "SecurityAlert",
    "SecurityIncident",
    "SentinelAudit",
    "SentinelHealth",
    "ThreatIntelligenceIndicator",
    "UrlClickEvents",
    "Watchlist"
]

def print_file_size(
        workspace_id: str,
):
    total_size = 0
    for table in LIST_TABLES:
        need_segement, row_per_query, total_count, total_size_table = check_segemented_query(workspace_id, table, (start_time, end_time))
        
        if total_count == -1 or total_size_table == -1:
            print(f"Table {table} is failed to get size.")
            continue

        total_size += total_size_table
        print(f"Table {table} has {total_count} rows and {round(total_size_table/1024/1024, 3)} MB   (GB: {round(total_size_table/1024/1024/1024, 3)})")

    print(f"Total size: {round(total_size/1024/1024, 3)} MB   (GB: {round(total_size/1024/1024/1024, 3)})")

# FirstActivityTime [UTC]                            8/1/2024, 12:26:22.000 PM
# LastActivityTime [UTC]                             8/1/2024, 12:37:30.277 PM
# extract 3 hours containing the attack
attacks = {
    322: {
        "start_time": datetime(2024, 8, 1, 11, 0, 0, 0, tzinfo=timezone.utc),
        "end_time": datetime(2024, 8, 1, 14, 0, 0, 0, tzinfo=timezone.utc),
    }
}

if __name__ == "__main__":
    ATEVET_17 = "0fbd2874-9307-4572-b499-f8fa3cc75daf"
    Alpine = "e34d562e-ef12-4c4e-9bc0-7c6ae357c015"

    # parameters
    # start_time = datetime(2024, 6, 18, 0, 0, 0, 0, tzinfo=timezone.utc)
    # end_time = datetime(2024, 8, 2, 0, 0, 0, 0, tzinfo=timezone.utc)
    # file_path = os.path.join(os.path.dirname(__file__), "data/alpineSkiHouse")

    start_time = attacks[322]["start_time"]
    end_time = attacks[322]["end_time"]
    # name: date+incident number
    file_path = os.path.join(os.path.dirname(__file__), "data/aug1_322")
    workspace_id = Alpine

    # print_file_size(Alpine)

    os.makedirs(file_path, exist_ok=True)
    for table in LIST_TABLES:
        if os.path.exists(os.path.join(file_path, f"{table}.csv")) or os.path.exists(os.path.join(file_path, table)):
            print(f"Table {table} is already saved.")
            continue
        try :
            query_and_save_data(workspace_id, table, (start_time, end_time), file_path, verbose=True)
        except HttpResponseError as e:
            print(f"Table {table} is failed to save.")
            print(e)
            continue
    