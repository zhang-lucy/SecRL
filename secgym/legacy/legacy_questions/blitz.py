qas_blitz = [
    # 02
    {
        "question": "Find OneNote executing `mshta` across all endpoints",
        "golden_query": """DeviceProcessEvents
| where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
| where InitiatingProcessVersionInfoOriginalFileName == 'OneNote.exe'
| where ProcessVersionInfoOriginalFileName == 'MSHTA.EXE'""",
        "tags": ["NLtoKQL"],
        "comments": "The problem is very good. I think besides evaluating the query, we should evaluate the output (dataframe) of the query as well."
    },
    {
        "question": "Find `mshta` which then executes another process that makes a network connection",
        "golden_query": """DeviceProcessEvents
| where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
| where InitiatingProcessVersionInfoOriginalFileName == 'MSHTA.EXE'
| join kind=inner ( 
    DeviceNetworkEvents 
    | where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
    | extend ProcessId = InitiatingProcessId 
) on ProcessId""",
        "tags": ["NLtoKQL"],
        "comments": "same as above."
    },

    {
        "context": "One of the first alerts in an incident report is related to a `ONENOTE.EXE` file executing some code. It seems to be potentially part of the threat actor's initial access tradecraft.",  
        "question":  "Can you find the relevant log(s) and analyze what happened?",
        "answer": "We can see that the `OneNote` document exported an HTA (HTML Application) file named `Urukhai.hta` which is then launched by `mshta` (Microsoft HTML Application Host).",
        "step": "02",
        "tags": ["open-ended"],
        "comments": "The problem here if we ignore the context is quite generic. Answer makes sense."
    },

     {
        "context": "We can see that a `OneNote` document exported an `HTA` (HTML Application) file named `Urukhai.hta` which is then launched by `mshta` (Microsoft HTML Application Host).",  
        "question": "What process was spawned from `mshta` and what did the process do?",
        "answer": "`PowerShell` was spawned. 1. Set the execution policy to unrestriced and hides the window, 2. download the `Invode-DoorBreach.ps1` script, 3. import the downloaded script as a module, 4. Executes the `invoke-DoorBreach` function.",
        "step": "02",
        "tags": ["open-ended"],
        "comments": "This is good."
     },

    {
        "step": 2,
        "context": "We found a Silver command and control (C2) connection established.",
        "question": "How did the attacker establish the C2 connection?",
        "answer":"The attacker established the C2 connection using the `Invoke-DoorBreach` script.",
        "tags": ["need_confirm"],
        "comments": "This is perfect!"
        
    },
    {
        "step": 2,
        "context": "We found an suspicious `Invoke-DoorBreach` script executed in the PowerShell logs.",
        "question": "Can you investigate with the evidence, and find what C2 (command and control) connection was used?",
        "answer":"The Sliver command and control (C2) connection was established.",
        "tags": ["need_confirm"],
        "comments": "Good"
    },
    {
        "step": 3,
        "context": "A suspicious `OneNote` file was found in the `Downloads` folder: `C:\\Users\\lrodriguez\\Downloads\\FestivalDeVina.one`.",
        "question": "How does it make it to the endpoint?",
        "answer": [
            "1. The file was downloaded by the `msedge.exe` process.",
            "2. The `msedge.exe` process was initiated by the `outlook.exe` process.",
            "3. We then verify that the link 'defenderatevet06-my.sharepoint.com/personal/sbeavers_peanutrecords_com/_layouts/15/download.aspx' is part of a phishing email",
            "4. We find the phishing email was sent by `sbeavers@peanutrecords.com`. We can infer that `Stevie Beavers` was compromised first or it is an insider job."
        ],
        "tags": ["hard", 'Multi-Step'],
        "comments": "Perfect for hard multi step eval. This should be one of the higher standard of questions we have in the dataset."
    },
    {
        "step": 3,
        "context": "A suspicious `OneNote` file was found in the `Downloads` folder: `C:\\Users\\lrodriguez\\Downloads\\FestivalDeVina.one`.",
        "question": "How was the file `FestivalDeVina.one` downloaded?",
        "answer": "The file `FestivalDeVina.one` was downloaded by the `msedge.exe` process.",
        "comments": "WHy no tag here? Seems like {confirm} tag?"
        # "tags":
    },
    {
        "step": 3,
        "context": "A suspicious `OneNote` file was found in the `Downloads` folder: `C:\\Users\\lrodriguez\\Downloads\\FestivalDeVina.one`.",
        "question": "We suspect this file was downloaded from a phishing email. Can you confirm this and find the sender of the email?",
        "answer": """The sender email is "sbeavers@peanutrecords.com". """,
        "tags": ["hard"],
        "comments": "good"
    },

    {
        "step": 3,
        "context": "A suspicious `OneNote` file was downloaded from the `msedge.exe` process.",
        "question": "What process initiated the browser to download the `OneNote`? What does this indicate?",
        "answer": "The process `outlook.exe` initiated `msedge.exe` to open the URL, indicating a likely phishing email.",
        "comments": "good. Why no tags here?"
    },
    {
        "step": 3,
        "context": "",
        "question": "Can you check where the suspicious link 'defenderatevet06-my.sharepoint.com/personal/sbeavers_peanutrecords_com/_layouts/15/download.aspx' was clicked?",
        "answer": "We can run the following query to validate that the link was clicked in the context of an email being delivered as part of a phishing campaign.",
        "golden_query": ["""
let url = "defenderatevet06-my.sharepoint.com/personal/sbeavers_peanutrecords_com/_layouts/15/download.aspx";
UrlClickEvents
| where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
| where Workload == 'Email'
| where ActionType == 'ClickAllowed'
| where Url has url
""",

    """let url = "defenderatevet06-my.sharepoint.com/personal/sbeavers_peanutrecords_com/_layouts/15/download.aspx";
UrlClickEvents
| where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
| where Workload == 'Email'
| where ActionType == 'ClickAllowed'
| where Url has url
| join kind=inner ( 
    EmailUrlInfo 
    | where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00)) 
) on NetworkMessageId
| project-reorder UrlLocation,UrlDomain,Url1"""]
    ,
    "comments": "Why 2 queries here?"
    },
    {
        "step": 3,
        "context": "We suspect the link clicked is part of a phishing email: defenderatevet06-my.sharepoint.com/personal/sbeavers_peanutrecords_com/_layouts/15/download.aspx",
        "question": "Can you identify the sender of the phishing email that contained the malicious URL?",
        "answer": [
            """1. We find the NetworkMessageId == '6e5740e4-5d51-4d17-574a-08db72e297c2'
```kql
let url = "defenderatevet06-my.sharepoint.com/personal/sbeavers_peanutrecords_com/_layouts/15/download.aspx";
UrlClickEvents
| where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
| where Workload == 'Email'
| where ActionType == 'ClickAllowed'
| where Url has url
```""",
            """2.The sender of the phishing email can be determined using:
  ```kql
  EmailEvents
  | where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
  | where NetworkMessageId == '6e5740e4-5d51-4d17-574a-08db72e297c2'
  | project-reorder SenderFromAddress, RecipientEmailAddress
  ```
  The results show that `sbeavers@peanutrecords.com` sent the phishing email."""
        ],
        "tags": ["hard", "Multi-Step"],
        "comments": "Here the kql to find the sender is mixed up with the actual answer. Maybe we should separate them out? But looks good otherwise."
    },

    {
        "step": 4,
        "context": "We found a malicious OneNote file `FestivalDeVina.one` was uploaded / created in the `sbeavers@peanutrecords.com` OneDrive and a download link was sent to `lrodriguez@peanutrecords.com`.",
        "question": "Please explore operations performed under the Microsoft OneDrive for Business and on Stevie's sharepoint folder. Based on the exploration, can you determine what API was used to upload the malicious OneNote file?",
        "answer": "the Microsoft Graph (00000003-0000-0000-c000-000000000000) API was used to perform this operation.",
        "comments": "good"
    },


    {
        "step": 5,
        "context": "We found that the Microsoft Graph (00000003-0000-0000-c000-000000000000) API was used to upload / create a malicious file 'FestivalDeVina.one' by 'sbeavers@peanutrecords.com'.",
        "question": "Can you check all the authentications specifying Microsoft Graph as the audience from this user?",
        "golden_query": """CloudAppEvents
| where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
| where ObjectName startswith 'https://defenderatevet06-my.sharepoint.com/personal/sbeavers_peanutrecords_com'
| where Application == 'Microsoft OneDrive for Business'
| where ObjectName endswith "FestivalDeVina.one"
| extend EventData = parse_json(RawEventData)
| extend Platform = EventData.Platform,ClientAppName = EventData.AppAccessContext.ClientAppName,
    AppId = tostring(EventData.AppAccessContext.ClientAppId),APIId = tostring(EventData.AppAccessContext.APIId),
    ClientIP = EventData.ClientIP,AuthenticationType = EventData.AuthenticationType,
    CorrelationId = tostring(EventData.CorrelationId),OperationTimeGenerated = TimeGenerated
| where AuthenticationType == 'OAuth'
| join kind=inner ( 
    SigninLogs 
    | where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
    | where Status.errorCode == 0
    | extend AccountId = UserId, APIId = ResourceIdentity
    | extend AuthTimeGenerated = TimeGenerated
) on AccountId,AppId,APIId
| project-reorder AuthTimeGenerated,OperationTimeGenerated,AuthenticationProtocol""",
        "tags": ["NLtoKQL"],
        "comments": "good."

    },

    {
        "step": 5,
        "context": "We now know that 'sbeavers@peanutrecords.com' authenticated Microsoft Graph (00000003-0000-0000-c000-000000000000) API to upload / create a malicious file 'FestivalDeVina.one'",
        "question": "We believe the attacker intiated the authentication through a phishing email. Can you find who sent the phishing email?",
        "answer": [
            """1. We first run the following query to look for those sign in events:
```kql
    CloudAppEvents
| where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
| where ObjectName startswith 'https://defenderatevet06-my.sharepoint.com/personal/sbeavers_peanutrecords_com'
| where Application == 'Microsoft OneDrive for Business'
| where ObjectName endswith "FestivalDeVina.one"
| extend EventData = parse_json(RawEventData)
| extend Platform = EventData.Platform,ClientAppName = EventData.AppAccessContext.ClientAppName,
    AppId = tostring(EventData.AppAccessContext.ClientAppId),APIId = tostring(EventData.AppAccessContext.APIId),
    ClientIP = EventData.ClientIP,AuthenticationType = EventData.AuthenticationType,
    CorrelationId = tostring(EventData.CorrelationId),OperationTimeGenerated = TimeGenerated
| where AuthenticationType == 'OAuth'
| join kind=inner ( 
    SigninLogs 
    | where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
    | where Status.errorCode == 0
    | extend AccountId = UserId, APIId = ResourceIdentity
    | extend AuthTimeGenerated = TimeGenerated
) on AccountId,AppId,APIId
| project-reorder AuthTimeGenerated,OperationTimeGenerated,AuthenticationProtocol
```
We can see in the results that the only sign in event with those characteristics was performed via the Device Code Authentication Flow. This attack requires the attacker to send the legitimate device code verification Url https://microsoft.com/devicelogin in the body of the phishing email so that the user goes through the Device Code Authentication Flow.
            """,
            """2. We can use the following query to look for evidence of this link: https://microsoft.com/devicelogin:
```kql 
let url = 'https://microsoft.com/devicelogin';
search in (EmailUrlInfo,UrlClickEvents,DeviceNetworkEvents,DeviceFileEvents,DeviceEvents)
TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
and (RemoteUrl has url
or FileOriginUrl has url
or FileOriginReferrerUrl has url
or Url has url
)
| take 100
| project-reorder TimeGenerated,Type,ActionType,UrlLocation,NetworkMessageId,
    InitiatingProcessAccountUpn,AccountUpn,InitiatingProcessFileName
            ```""",
            """3. We can see in the results that the initial phishing email was sent by azure-noreply@microsoft.com, but it was categorized as Phish:["Spoof DMARC"]. We found our true initial access."""
        ],
        "tags": ["hard", "Multi-Step"],
        "comments": "good"

    },

    {
        # Step 4 and 5
        "step": 5,
        "context": "We fine a malicious OneNote file `FestivalDeVina.one` was uploaded / created in the` sbeavers@peanutrecords.com`'s OneDrive.",
        "question": "Can you tell if this is an insider job, or a compromised account?",
        "answer": [
            """1. We explore operations performed under the `Microsoft OneDrive for Business` and on Stevie's sharepoint folder, and find that the file was created with `Microsoft Graph`.""",
            """2. We then look into authentications specifying `Microsoft Graph` as the audience. We find that the only sign-in event with those characteristics was performed via the `Device Code Authentication Flow`. This indicates Stevie might have been part of a Device Code Phishing attack.""",
            """3. This attack requires the attacker to send the legitimate device code verification Url `https://microsoft.com/devicelogin`. We look into emails and found that this link was part of a phishing email sent by `azure-noreply@microsoft.com`, but categorized as Phish:['Spoof DMARC'].""",
            """4. We can confirm that this is a compromised account, and the attacker used a phishing email to compromise Stevie Beavers."""
        ],
        "tag": ["hard", "Multi-Step"],
        "comments": "good."
    },


    {
        "step": 6,
        "question": "Write a query to explore all the network activity to IP address `192.168.3.5`.",
        "golden_query": """DeviceNetworkEvents
| where Timestamp between (datetime(2023-09-22T00:00:00) .. datetime(2023-10-23T00:00:00))
| where RemoteIP == '192.168.3.5'""",
        "tags": ["NLtoKQL"],
        "comments": "This can be part of general questions but good."
    },
    {
        "step": 7,
        "question": "Write a query to get all LDAP queries made by processes spawned by the SLiver binary DoorBreach.exe",
        "golden_query": """DeviceEvents
| where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
| where ActionType == 'LdapSearch'
| where InitiatingProcessParentFileName == 'DoorBreach.exe'""",
        "tags": ["NLtoKQL"],
        "comments": "good. "
    },


    {
        "step": 8,
        "context": "We found that malicious script executed on 'WORKSTATION8.peanutrecords.com' downloaded a compressed file to the Windows Temp folder using a function `Get-Artillery`. The contents extracted to the ProgramData directory: C:\\ProgramData\\PRGPOs",
        "question": "Write a query to check if that folder was used in any scripts (i.e. PowerShell) on the same endpoint.",
        "golden_qeury": """WindowsEvent
| where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
| where Computer == 'WORKSTATION8.peanutrecords.com'
| where Provider == 'Microsoft-Windows-PowerShell'
| where EventID == 4104
| extend ScriptBlockText = EventData.ScriptBlockText
| where ScriptBlockText contains 'PRGPOs'
| project-reorder TimeGenerated,ScriptBlockText""",
        "tags": ["NLtoKQL"],
        "comments": "good"
    },
    {
        "step": 8,
        "context": "We found that malicious script executed on 'WORKSTATION8.peanutrecords.com' downloaded a compressed file to the Windows Temp folder using a function `Get-Artillery`. The contents extracted to the ProgramData directory: C:\\ProgramData\\PRGPOs",
        "question": "Can you check on events to see if there are any other malicious behaviors regarding this folder?",
        "answer": "The folder contains a backed-up Group Policy Object (GPO) named `ManeuverWarfare` that gets imported via the `Import-GPO` PowerShell Cmdlet to the Domain and attach to the `Workstations` AD organizational unit. This allows the threat actor to spread specific settings to all endpoints in the domain.",
        "comments": "good"
    },

    {
        "step": 9,
        "context": "The folder contains a backed-up Group Policy Object (GPO) named `ManeuverWarfare` that gets imported via the `Import-GPO` PowerShell Cmdlet to the Domain and attach to the `Workstations` AD organizational unit. This allows the threat actor to spread specific settings to all endpoints in the domain.",
        "question": "Can you check if GPO is applied to the comprised endpoint 'WORKSTATION8.peanutrecords.com'?",
        "answer": """Yes. Query:
```kql
WindowsEvent
| where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
| where Computer == 'WORKSTATION8.peanutrecords.com'
| where Provider == 'Microsoft-Windows-Sysmon'
| where EventID == 13
| where EventData.TargetObject startswith 
    "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Group Policy\\DataStore\\Machine"
| where EventData.Details == 'ManeuverWarfare' and EventData.EventType == 'SetValue'
```,
"comments": "good"
"""
    },
    {
        "step": 9,
        "question": "Can you see if the threat actor potentially force a Group Policy update with built-in commands such as gpupdate on the compromised endpoint 'workstation8.peanutrecords.com'? What do you find?",
        "answer": """
```kql
DeviceProcessEvents
| where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
| where DeviceName == 'workstation8.peanutrecords.com'
| where ProcessCommandLine contains 'gpupdate'
| where InitiatingProcessCommandLine != 'svchost.exe -k netsvcs -p -s Schedule'
| project-reorder TimeGenerated,ProcessCommandLine,InitiatingProcessCommandLine
```
We can see that the threat actor was using LDAP queries to enumerate endpoints and WMI to force a Group Policy update on all of those endpoints""",
"comments": "good"
    },
    

    {
        "step": 10,
        "context": "Following the investigation, we can see a Suspicious Scheduled Task Process Launched alert which points to PowerShell executing a script.",
        "question": "Can you check what Scheduled Tasks were created?",
        "answer": "We can see the `BlitzConfig` scheduled task being created on all the workstations.",
        "comments": "good. Again without context the question is generic."
    }
]

# nltosql_count = 0
# multi_count = 0
# for qa in qas_blitz:
#     if "tags" in qa:
#         if "NLtoKQL" in qa["tags"]:
#             nltosql_count += 1
#         if "Multi-Step" in qa["tags"]:
#             multi_count += 1
# print("NLtoKQL count: ", nltosql_count)
# print("Multi-Step count: ", multi_count)        
# print(len(qas_blitz))

if __name__ == '__main__':
    with open("blitz_ransomware_qa.json", "w") as f:
        import json
        json.dump(qas_blitz, f, indent=4)