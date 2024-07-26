aadcomp = [
    {
        "question": "A potential malicious user is using Graph API to retrieve data. How many queries were executed successfully?",
        "answer": "3",
        "tags": [
            "NLtoKQL"
        ]
    },
    {
        "question": "A potential malicious user is using Graph API to enumerate all users in the tenant. Find the ServicePrincipalId that is doing this.",
        "answer": "cb006143-fbfb-41eb-b62d-b88fb697cdce",
        "tags": [
            "NLtoKQL"
        ]
    },
    {
        "question": "In this incident, a credential is added to a applications that have the mail.read role. What is the name of the application?",
        "golden_query": """AuditLogs 
| where TimeGenerated between(datetime(2024-06-24 17:42:13) .. datetime(2024-06-24 17:50:29))
| where OperationName has_any ("Add service principal", "Certificates and secrets management")  
| where Result =~ "success"  
| where tostring(InitiatedBy.user.userPrincipalName) has "@" or tostring(InitiatedBy.app.displayName) has "@"  
| mv-expand TargetResources 
| extend info = tostring(TargetResources.id)""",
        "golden_sql": """SELECT *
FROM AuditLogs
WHERE TimeGenerated BETWEEN '2024-06-24 10:42:13' AND '2024-06-24 10:50:29'
  AND (
    LOWER(OperationName) LIKE '%add service principal%' OR
    LOWER(OperationName) LIKE '%certificates and secrets management%'
  )
  AND LOWER(Result) = 'success';""",
        "answer": "ARTBAS AAD App",
    },
]


print("a")

with open("aad_comprise_qa.json", "w") as f:
    import json
    json.dump(aadcomp, f, indent=4)
print("a")