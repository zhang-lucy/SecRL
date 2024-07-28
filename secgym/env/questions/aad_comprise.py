report = """
Given: There is a suspicious email reading event, where the emails are read with Graph API through a previously unknown application registration.

----------------------------------------------------------------------------------------------------------------------------
## Investigation 1: Check table `OfficeActivity` with Graph API's id for mail read events.
```kql
OfficeActivity
| where Operation == "MailItemsAccessed" and AppId == "00000003-0000-0000-c000-000000000000"
```
```sql
SELECT *
FROM OfficeActivity
WHERE Operation = 'MailItemsAccessed' AND AppId = '00000003-0000-0000-c000-000000000000'
```

### I1.IoC
1. ClientAppId: bb77fe0b-52af-4f26-9bc7-19aa48854ebf
2. MailboxOwnerUPN: mmelendez@DefenderATEVET17.onmicrosoft.com
   - the user's mailbox who was accessed.

----------------------------------------------------------------------------------------------------------------------------
## Investigation 2: Check table `SecurityExposureManagement` to find more information about the client app with that ID.
### I2.IoC 
1. ObjectId: 47dee0a2-d662-4664-acfa-a28bb62bdbc0

----------------------------------------------------------------------------------------------------------------------------
## Investigation 3: Check `AADServicePrincipalSignInLogs` to identify the last time this client app with `ClientAppId` was authenticated.
- From I1.IoC1
```kql
AADServicePrincipalSignInLogs
| where AppId == "bb77fe0b-52af-4f26-9bc7-19aa48854ebf"
```

### I3.IoC
1. IPAddress: 72.43.121.34
    - From the above query, we identify a new IOC: The IPAdress where the service principal authenticated from is found 72.43.121.34

----------------------------------------------------------------------------------------------------------------------------
## Investigation 4: Check `SigninLogs` for other authentication events from the same IP address.
- From A3.IoC1
```kql
let ipAddress = "72.43.121.43";
SigninLogs
    | where IPAddress == ipAddress
    | project TimeGenerated, IPAddress, UserPrincipalName, ResultType, ResultDescription, AuthenticationRequirement, ConditionalAccessStatus,  ResourceDisplayName, AppDisplayName, ResourceIdentity, ClientAppUsed, RiskLevelAggregated, RiskLevelDuringSignIn, RiskState, RiskEventTypes
```
### I4.IoC
- Multiple users are authenticating from the same IP address but failed. There is one account that successfully authenticated from this account: mvelazco@defender...

----------------------------------------------------------------------------------------------------------------------------
## Investigation 5: Check `AuditLogs` for the latest actions that have occurred to this application registration: modifications, updates, etc.
- From I2.IoC1

```kql
AuditLogs
| mv-expand TargetResource = TargetResources
| extend TargetResourceJson = parse_json(TargetResource)
| where TargetResourceJson.id == "47dee0a2-d662-4664-acfa-a28bb62bdbc0"
```

### IoC
- We learn that there were certain changes made against the application. Specifically, new credentials were added to the application registration right before it authenticated.

----------------------------------------------------------------------------------------------------------------------------
## Investigation 6: We check other activities with the same IP address, like Microsoft Graph API requests.
- From I3.IoC1
```kql
MicrosoftGraphActivityLogs
| where RequestUri endswith "/users" or RequestUri endswith "/applications"  
| where  IPAddress == "72.43.121.43"
```

### I6.IoC
- We find that the same IP address is making requests to the Microsoft Graph API for both users and applications. 
"""

aad_comprise_qa = [
    {
        "difficulty": "Easy",

        "context": "There is a suspicious email reading event, where the emails are read with Graph API through a previously unknown application registration.",
        "question": "what is the ID of the client application that is used to access the Microsoft Graph API?",
        "answer": "bb77fe0b-52af-4f26-9bc7-19aa48854ebf",
        "solution": "1. Check table `OfficeActivity` with the Graph API's id for mail read events. \n2. The client application ID is `bb77fe0b-52af-4f26-9bc7-19aa48854ebf`.",

        "start_node": "1",
        "end_node": "2",
        "hop": "1"
    },
    {
        "difficulty": "Medium",
        
        "context": "There is a suspicious email reading event, where the emails are read with Graph API through a previously unknown application registration.",
        "question": "What is the Object ID of the client application that is used to access the Microsoft Graph API?",
        "answer": "47dee0a2-d662-4664-acfa-a28bb62bdbc0",
        "solution": "1. The email is read by client application with id: `bb77fe0b-52af-4f26-9bc7-19aa48854ebf`. \n2. From the security graph table, we can map the client to be `47dee0a2-d662-4664-acfa-a28bb62bdbc0`",
        
        "start_node": "1",
        "end_node": "3",
        "hop": "2"
    },
    {
        "difficulty": "Medium",
        
        "context": "There is a suspicious email reading event, where the emails are read with Graph API through a previously unknown application registration.",
        "question": "What is the name of the client application?",
        "answer": "ReadEmailEWS",
        "start_node": "1",
        "end_node": "4",
        "hop": "2",
        "comment": "this question is basically the same as last one: 1. query the email log. 2. identify client app 2. from the app find the servicepricinipal singin logs 3. find the answer from the log. It is just this answer is an IOC, instead of a random entry."
    },
    {
        "difficulty": "Medium",
        
        "context": "There is a suspicious email reading event, where the emails are read with Graph API through a previously unknown application registration.",
        "question": "what is the IP address of the user that is used to perform this email reading activity?",
        "answer": "72.43.121.43",
        "solution": "1. The email is read by user `mvelazco@DefenderATEVET17.onmicrosoft.com`.\n2. This ID is logged in with IP address: 72.43.121.43.",
        
        "start_node": "1",
        "end_node": "5",
        "hop": "3",
        "comment": "TODO: The user info is not in the graph yet."
    },
    {
        "difficulty": "Hard",
        "context": "There is a suspicious email reading event, where the emails are read with Graph API through a previously unknown application registration.",
        "question": "When did the user gain access to the client app?",
        "solution": "1. The email is read with the client application ID: bb77fe0b-52af-4f26-9bc7-19aa48854ebf. \n2. This ID is the client application `ReadEmailEWS`. \n3. A credential was added to this client application at <TIME>",
        "start_node": "1",
        "end_node": "6",
        "hop": "4"
    },
    {
        "difficulty": "Hard",
        "context": "We have found that an attacker is reading emails with a client application.",
        "question": "Which technique did this attacker used to gain initial access to the tenant?",
        "answer": "password spray attack",
        "solution": "1. The email is read by user `mvelazco@DefenderATEVET17.onmicrosoft.com`.\n2. This ID is logged in with IP address: 72.43.121.43. \n3.From the same IP address, there are several attempted logins ins with different usernames but failed.\n 4. The attacker used password spray attack to gain access to the tenant.",
        "start_node": "1",
        "end_node": "7",
        "hop": "4"
    },
    {
        "difficulty": "Hard",
        "context": "We have found that an attacker is reading emails with a client application.",
        "question": "What other suspicious activity was performed by the same client application?",
        "answer": "Enumerate users and applications with Graph API",
        "solution": "1. The email is read with the client application ID: `bb77fe0b-52af-4f26-9bc7-19aa48854ebf`. \n2. We look through different logs and find that this client application is also used to enumerate all users and applications with Graph API.",
        "start_node": "1",
        "end_node": "7",
        "hop": "4"
    },
    {
        "difficulty": "Easy",
        
        "context": "There is a suspicious reading of emails through client application with ID: `bb77fe0b-52af-4f26-9bc7-19aa48854ebf`.",
        "question": "What is the Object ID of the client application that is used to access the Microsoft Graph API?",
        "answer": "47dee0a2-d662-4664-acfa-a28bb62bdbc0",
        "solution": "From the security graph table, we can map the client to be `47dee0a2-d662-4664-acfa-a28bb62bdbc0`",
        "start_node": "2",
        "end_node": "3",
        "hop": "1"
    },
    {
        "difficulty": "Easy",
        
        "context": "There is a suspicious reading of emails through a client application with ID: `bb77fe0b-52af-4f26-9bc7-19aa48854ebf`.",
        "question": "What is the name of the client application?",
        "answer": "ReadEmailEWS",
        "start_node": "2",
        "end_node": "4",
        "hop": "1",
        "comment": "this question is basically the same as last one: 1. query the email log. 2. identify client app 2. from the app find the servicepricinipal singin logs 3. find the answer from the log. It is just this answer is an IOC, instead of a random entry."
    },
    {
        "difficulty": "Easy",
        
        "context": "There is a suspicious reading of emails using Microsoft Graph API by user `mvelazco@DefenderATEVET17.onmicrosoft.com`",
        "question": "what is the IP address of the user that is used to perform this email reading activity?",
        "answer": "72.43.121.43",
        "start_node": "2",
        "end_node": "5",
        "hop": "1"
    },
    {
        "difficulty": "Medium",
        
        "context": "There is a suspicious reading of emails through a client application with ID: `bb77fe0b-52af-4f26-9bc7-19aa48854ebf`.",
        "question": "When did the user add a credential to the client app?",
        "solution": "1. This ID is the client application `ReadEmailEWS`. \n2. A credential was added to this client application at <TIME>",
        "start_node": "2",
        "end_node": "6",
        "hop": "2",
        "comment": "The first step might be changed. Basically mapping application id to the app's other info to be used for querying the time."
    },
    {
        "difficulty": "Hard",
        "context": "We have found that an attacker with user id `mvelazco@DefenderATEVET17.onmicrosoft.com` reading emails using Microsoft Graph API",
        "question": "Which technique did this attacker used to gain initial access to the tenant?",
        "answer": "password spray attack",
        "solution": "1. This ID is logged in with IP address: 72.43.121.43. \n2.From the same IP address, there are several attempted logins ins with different usernames but failed.\n3. The attacker used password spray attack to gain access to the tenant.",
        "start_node": "2",
        "end_node": "7",
        "hop": "3"
    },
    {
        "difficulty": "Medium",
        "context": "There is a suspicious reading of emails through a client application with ID: `bb77fe0b-52af-4f26-9bc7-19aa48854ebf`.",
        "question": "What other suspicious activity was performed by the same client application?",
        "answer": "Enumerate users and applications with Graph API",
        "solution": "We look through different logs and find that this client application is also used to enumerate all users and applications with Graph API.",
        "start_node": "2",
        "end_node": "8",
        "hop": "1"
    },
    {
        "difficulty": "Easy",
        
        "context": "There is a suspicious reading of emails using Microsoft Graph API by user `mvelazco@DefenderATEVET17.onmicrosoft.com`",
        "question": "what is the IP address of the user that is used to perform this email reading activity?",
        "answer": "72.43.121.43",
        "start_node": "3",
        "end_node": "5",
        "hop": "1"
    },
    {
        "difficulty": "Easy",
        
        "context": "A user authenticated the app with ID `bb77fe0b-52af-4f26-9bc7-19aa48854ebf`.",
        "question": "When did the user added credential to the app?",
        "answer": "<TIME>",
        "solution": "A credential was added to this client application at <TIME>",
        "start_node": "3",
        "end_node": "6",
        "hop": "1",
        "comment": "The first step might be changed. Basically mapping application id to the app's other info to be used for querying the time."
    },
    {
        "difficulty": "Medium",
        "context": "We have found that an attacker with IP address: 72.43.121.43 reading emails using Microsoft Graph API.",
        "question": "Which technique did this attacker used to gain initial access to the tenant?",
        "answer": "password spray attack",
        "solution": "1.From the same IP address, there are several attempted logins ins with different usernames but failed.\n2. The attacker used password spray attack to gain access to the tenant.",
        "start_node": "3",
        "end_node": "7",
        "hop": "2"
    },
    {
        "difficulty": "Medium",
        "context": "We have found that a suspicious client application with name `ReadEmailEWS` is reading emails using Microsoft Graph API.",
        "question": "What other suspicious activity was performed by the same client application?",
        "answer": "Enumerate users and applications with Graph API",
        "solution": "We look through different logs and find that this client application is also used to enumerate all users and applications with Graph API.",
        "start_node": "3",
        "end_node": "8",
        "hop": "1"
    },
    {
        "difficulty": "Easy",
        
        "context": "",
        "question": "When was a new credential added to the app `ReadEmailEWS`?",
        "answer": "<TIME>",
        "solution": "A credential was added to this client application at <TIME>",
        "start_node": "4",
        "end_node": "6",
        "hop": "1",
        "comment": "The first step might be changed. Basically mapping application id to the app's other info to be used for querying the time."
    },
    {
        "difficulty": "Easy",
        "context": "",
        "question": "Is there any suspicious login activity from the IP address `72.43.121.43`? What is it?",
        "answer": "Yes, password spray attack.",
        "solution": "Yes, the same IP address has attempted to log in with different usernames. It is likely a password spray attack.",
        "start_node": "5",
        "end_node": "6",
        "hop": "1"
    },
    {
        "difficulty": "Easy",
        
        "context": "A client app is using Microsoft Graph API to enumerate users and applications.",
        "question": "what is the ID of the client application that is used to access the Microsoft Graph API?",
        "answer": "bb77fe0b-52af-4f26-9bc7-19aa48854ebf",
        "start_node": "8",
        "end_node": "2",
        "hop": "1"
    },
    {
        "difficulty": "Medium",
        
        "context": "A client app is using Microsoft Graph API to enumerate users and applications.",
        "question": "What is the Object ID of the client application that is used to access the Microsoft Graph API?",
        "answer": "47dee0a2-d662-4664-acfa-a28bb62bdbc0",
        "solution": "1. The email is read by client application with id: `bb77fe0b-52af-4f26-9bc7-19aa48854ebf`. \n2. From the security graph table, we can map the client to be `47dee0a2-d662-4664-acfa-a28bb62bdbc0`",
        "start_node": "8",
        "end_node": "3",
        "hop": "2"
    },
    {
        "difficulty": "Medium",
        
        "context": "A client app is using Microsoft Graph API to enumerate users and applications.",
        "question": "What is the name of the client application?",
        "answer": "ReadEmailEWS",
        "start_node": "8",
        "end_node": "4",
        "hop": "2",
        "comment": "this question is basically the same as last one: 1. query the email log. 2. identify client app 2. from the app find the servicepricinipal singin logs 3. find the answer from the log. It is just this answer is an IOC, instead of a random entry."
    },
    {
        "difficulty": "Medium",
        
        "context": "A client app is using Microsoft Graph API to enumerate users and applications.",
        "question": "what is the IP address of the user that is used to perform this activity?",
        "answer": "72.43.121.43",
        "solution": "1. The activity is performed by user `mvelazco@DefenderATEVET17.onmicrosoft.com`.\n2. This ID is logged in with IP address: 72.43.121.43.",
        "start_node": "1",
        "end_node": "5",
        "hop": "3",
        "comment": "TODO: The user info is not in the graph yet."
    },
    {
        "difficulty": "Hard",
        "context": "A client app is using Microsoft Graph API to enumerate users and applications.",
        "question": "When did the user gain access to the client app?",
        "solution": "1. The enumeration is performed by the app with the client application ID: `bb77fe0b-52af-4f26-9bc7-19aa48854ebf`. \n2. This ID is the client application `ReadEmailEWS`. \n3. A credential was added to this client application at <TIME>",
        "start_node": "8",
        "end_node": "6",
        "hop": "4"
    },
    {
        "difficulty": "Hard",
        "context": "We have found an attacker enumerating users and applications with a client application.",
        "question": "Which technique did this attacker used to gain initial access to the tenant?",
        "answer": "password spray attack",
        "solution": "1. The activity is performed by user `mvelazco@DefenderATEVET17.onmicrosoft.com`.\n2. This ID is logged in with IP address: 72.43.121.43. \n3.From the same IP address, there are several attempted logins ins with different usernames but failed.\n 4. The attacker used password spray attack to gain access to the tenant.",
        "start_node": "8",
        "end_node": "7",
        "hop": "4"
    },
    {
        "difficulty": "Hard",
        "context": "We have found an attacker enumerating users and applications with a client application.",
        "question": "What other suspicious activity was performed by the same client application?",
        "answer": "Enumerate users and applications with Graph API",
        "solution": "1.The enumeration is performed by the app with the client application ID: `bb77fe0b-52af-4f26-9bc7-19aa48854ebf`. \n2. We look through different logs and find that this client application is also used to read emails with Graph API.",
        "start_node": "8",
        "end_node": "1",
        "hop": "2"
    }
]

#     {
#         "context": "There is a suspicious reading of emails using Microsoft Graph API.",
#         "question": "How did the user gain access to read the emails?",
#         "answer": "1. The email is read with the client application ID: bb77fe0b-52af-4f26-9bc7-19aa48854ebf. \n2. This ID is the client application `ReadEmailEWS`. \n3. A credential was added to this client application. ",
#         "start_node": "Activity 1",
#         "end_node": "IOC 1",
#         "hop": "3"
#     },

#     {

#         "context": "",
#         "question": "Check if there is one IP address that failed to authenticate with multiple accounts.",
#         "answer": "Yes. 72.43.121.43",
#         "start_node": "IOC",
#         "end_node": "IOC 1",
#         "hop": "1"
#     },

#     {
#         "context": "There is a suspicious reading of emails using Microsoft Graph API.",
#         "question": "What is the user agent of the client application that is used to access the Microsoft Graph API?",
#         "answer": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299",
#         "start_node": "1",
#         "end_node": "4",
#         "hop": "3"
#     }
# ]


if __name__ == '__main__':
    with open("aad_comprise_qa.json", "w") as f:
        import json
        json.dump(aad_comprise_qa, f, indent=4)