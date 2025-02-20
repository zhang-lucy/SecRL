from secgym.env.download_logs import download_logs, to_abs_path
import os
from datetime import datetime, timedelta, timezone
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
    "OfficeActivity",

    # "SecurityAlert",
    # "SecurityEvent",
]


if __name__ == "__main__":
    ATEVET_17 = "0fbd2874-9307-4572-b499-f8fa3cc75daf"

    root_path = os.path.join(os.path.dirname(__file__), "final_data")

    file_path = to_abs_path("data/addcomp_jul25")
    start_time = datetime(2024, 7, 25, 15, 0, 0, 0, tzinfo=timezone.utc)
    # for 3 hours
    duration = timedelta(hours=3)
    end_time = start_time + duration

    download_logs(workspace_id=ATEVET_17, start_time=start_time, end_time=end_time, list_tables=LIST_TABLES, file_path=file_path)