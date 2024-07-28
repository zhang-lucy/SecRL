# Report on AAD Comprise
## A1 (Activity 1)
**Link From:**  Existing Alert   
There is a suspicious email reading event, where the emails are read with Graph API through a client application.The application is new and was never used to read emails before.
```kql
OfficeActivity
| where Operation == "MailItemsAccessed" and AppId == "00000003-0000-0000-c000-000000000000"
```

- **A1.IoC1**: ClientAppId: bb77fe0b-52af-4f26-9bc7-19aa48854ebf   
  (Q1: Investigate more with 1.1)   
  (Q2: Find authentication events with 1.1)      
  (Q3: Check auditlogs, When was a credential added with this ClientAppID?)      


## A2
**Link From:** A1.IoC1
We check the last time this client app with `ClientAppId` was authenticated.
```kql
AADServicePrincipalSignInLogs
```

- **A2.IoC1**: The service name is `ReadEmailEWS` that uses Graph API. 

- **A2.IoC2**: IP Address: 72.43.121.44

## A3
Link From: The service name is `ReadEmailEWS` that uses Graph API. 

A credential added is added to the client APP `ReadEmailEWS`
```kql
AuditLogs
| where OperationName contains "Update application – Certificates and secrets management"
```

- **A3.IoC1**: N/A

## A4
Link From: **A2.IoC2**: IP Address: 72.43.121.44

We check other suspicious activities from the same IP address and found a password spray attack.
```kql
SigninLogs
| where ResultType == 50126
| project TimeGenerated, UserPrincipalName, AppDisplayName, ClientAppUsed, IPAddress, Location, Status
| order by TimeGenerated desc

SigninLogs
| where ResultType == "50126" or ResultType == "50076" // Add other relevant failure result types if needed
| extend IPAddress = tostring(IPAddress)
| summarize UniqueUsers = dcount(UserPrincipalName), AttemptedUsers = make_set(UserPrincipalName) by IPAddress, bin(TimeGenerated, 10m)
| where UniqueUsers > 5
| project TimeGenerated, IPAddress, UniqueUsers, AttemptedUsers

```

## A5
Link From: **A1.IoC1**: ClientAppId: bb77fe0b-52af-4f26-9bc7-19aa48854ebf

The same client app is used to enumerate users and applications with Graph API.

```kql
MicrosoftGraphActivityLogs
| where RequestUri endswith "/users" and RequestMethod == "GET"

MicrosoftGraphActivityLogs
| where RequestUri endswith "/applications" and RequestMethod == "GET"

| where AppId == "bb77fe0b-52af-4f26-9bc7-19aa48854ebf"
```





