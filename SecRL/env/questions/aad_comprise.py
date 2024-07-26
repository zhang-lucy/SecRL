
# activity1 = soc_graph.add_activity("A1: Suspicious email reading event through Graph API")
# ioc1_a1 = soc_graph.add_ioc("A1.IoC1: ClientAppId: bb77fe0b-52af-4f26-9bc7-19aa48854ebf", from_activity_id=activity1)

# # A2
# activity2 = soc_graph.add_activity("A2: Check last authentication time of client app", from_ioc_id=ioc1_a1)
# ioc1_a2 = soc_graph.add_ioc("A2.IoC1: Service name: ReadEmailEWS using Graph API", from_activity_id=activity2)
# ioc2_a2 = soc_graph.add_ioc("A2.IoC2: IP Address: 72.43.121.44", from_activity_id=activity2)

# # A3
# activity3 = soc_graph.add_activity("A3: Credential added to client app ReadEmailEWS", from_ioc_id=ioc1_a2)

# # A4
# activity4 = soc_graph.add_activity("A4: Password spray attack from IP address 72.43.121.44", from_ioc_id=ioc2_a2)

# # A5
# activity5 = soc_graph.add_activity("A5: Client app used to enumerate users and applications with Graph API", from_ioc_id=ioc1_a1)


aad_comprise_qa = [
    {
        "difficulty": "Easy",
        "type": "single response",

        "context": "There is a suspicious reading of emails with a client application.",
        "question": "what is the ID of the client application that is used to access the Microsoft Graph API?",
        "answer": "bb77fe0b-52af-4f26-9bc7-19aa48854ebf",

        "start_node": "1",
        "end_node": "2",
        "hop": "1",
    },

    {
        "difficulty": "Medium",
        "type": "single response",

        "context": "There is a suspicious reading of emails with a client application.",
        "question": "On which city is this client application authenticated?",
        "answer": "Dublin",
        "solution": "1. The email is read by client application with id: `bb77fe0b-52af-4f26-9bc7-19aa48854ebf`. \n2. This client application is authenticated in Dublin.",

        "start_node": "1",
        "end_node": "3",
        "hop": "2",
    },

    {
        "difficulty": "Medium",
        "type": "single response",

        "context": "There is a suspicious reading of emails with a client application.",
        "question": "What is the name of the client application?",
        "answer": "ReadEmailEWS",

        "start_node": "1",
        "end_node": "4",
        "hop": "2",

        "comment": "this question is basically the same as last one: 1. query the email log. 2. identify client app 2. from the app find the servicepricinipal singin logs 3. find the answer from the log. It is just this answer is an IOC, instead of a random entry."
    },

    {
        "difficulty": "Medium",
        "type": "single response",

        "context": "There is a suspicious reading of emails with a client application.",
        "question": "what is the IP address of the user that is used to perform this email reading activity?",
        "answer": "72.43.121.44",
        "solution": "1. The email is read by user `mvelazco@DefenderATEVET17.onmicrosoft.com`.\n2. This ID is logged in with IP address: 72.43.121.44.",

        "start_node": "1",
        "end_node": "5",
        "hop": "3",

        "comment": "TODO: The user info is not in the graph yet."
    },

    {
        "difficulty": "Hard",
        "type": "free response",
        "context": "There is a suspicious reading of emails with a client application.",
        "question": "When did the user gain access to the client app?",
        "solution": "1. The email is read with the client application ID: bb77fe0b-52af-4f26-9bc7-19aa48854ebf. \n2. This ID is the client application `ReadEmailEWS`. \n3. A credential was added to this client application at <TIME>",
        "start_node": "1",
        "end_node": "6",
        "hop": "4",
    },

    {
        "difficulty": "Hard",
        "type": "free response",
        "context": "We have found that an attacker is reading emails with a client application.",
        "question": "Which technique did this attacker used to gain initial access to the tenant?",
        "answer": "password spray attack",

        "solution": "1. The email is read by user `mvelazco@DefenderATEVET17.onmicrosoft.com`.\n2. This ID is logged in with IP address: 72.43.121.44. \n3.From the same IP address, there are several attempted logins ins with different usernames but failed.\n 4. The attacker used password spray attack to gain access to the tenant.",

        "start_node": "1",
        "end_node": "7",
        "hop": "4",
    },


    {
        "difficulty": "Hard",
        "type": "general response",
        "context": "We have found that an attacker is reading emails with a client application.",
        "question": "What other suspicious activity was performed by the same client application?",
        "answer": "Enumerate users and applications with Graph API",

        "solution": "1. The email is read with the client application ID: `bb77fe0b-52af-4f26-9bc7-19aa48854ebf`. \n2. We look through different logs and find that this client application is also used to enumerate all users and applications with Graph API.",

        "start_node": "1",
        "end_node": "7",
        "hop": "4",
    },

    # ------------------------------------------Start at 2

    {
        "difficulty": "Easy",
        "type": "single response",

        "context": "There is a suspicious reading of emails through client application with ID: `bb77fe0b-52af-4f26-9bc7-19aa48854ebf`.",
        "question": "On which city is this client application authenticated?",
        "answer": "Dublin",
        "solution": "1. This client application is authenticated in Dublin.",

        "start_node": "2",
        "end_node": "3",
        "hop": "1",
    },

    {
        "difficulty": "Easy",
        "type": "single response",

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
        "type": "single response",

        "context": "There is a suspicious reading of emails using Microsoft Graph API by user `mvelazco@DefenderATEVET17.onmicrosoft.com`",
        "question": "what is the IP address of the user that is used to perform this email reading activity?",
        "answer": "72.43.121.44",

        "start_node": "2",
        "end_node": "5",
        "hop": "1",
    },

    {
        "difficulty": "Medium",
        "type": "single response",
        "context": "There is a suspicious reading of emails through a client application with ID: `bb77fe0b-52af-4f26-9bc7-19aa48854ebf`.",
        "question": "When did the user gain access to the client app?",
        "solution": "1. This ID is the client application `ReadEmailEWS`. \n2. A credential was added to this client application at <TIME>",
        "start_node": "2",
        "end_node": "6",
        "hop": "2",

        "comment": "The first step might be changed. Basically mapping application id to the app's other info to be used for querying the time."
    },

    {
        "difficulty": "Hard",
        "type": "free response",
        "context": "We have found that an attacker with user id `mvelazco@DefenderATEVET17.onmicrosoft.com` reading emails using Microsoft Graph API",
        "question": "Which technique did this attacker used to gain initial access to the tenant?",
        "answer": "password spray attack",

        "solution": "1. This ID is logged in with IP address: 72.43.121.44. \n2.From the same IP address, there are several attempted logins ins with different usernames but failed.\n3. The attacker used password spray attack to gain access to the tenant.",

        "start_node": "2",
        "end_node": "7",
        "hop": "3",
    },


    {
        "difficulty": "Medium",
        "type": "general response",
        "context": "There is a suspicious reading of emails through a client application with ID: `bb77fe0b-52af-4f26-9bc7-19aa48854ebf`.",
        "question": "What other suspicious activity was performed by the same client application?",
        "answer": "Enumerate users and applications with Graph API",

        "solution": "We look through different logs and find that this client application is also used to enumerate all users and applications with Graph API.",

        "start_node": "2",
        "end_node": "8",
        "hop": "1",
    },

    # ------------------------------------------start at node 3


    {
        "difficulty": "Easy",
        "type": "single response",

        "context": "There is a suspicious reading of emails using Microsoft Graph API by user `mvelazco@DefenderATEVET17.onmicrosoft.com`",
        "question": "what is the IP address of the user that is used to perform this email reading activity?",
        "answer": "72.43.121.44",

        "start_node": "3",
        "end_node": "5",
        "hop": "1",
    },

    {
        "difficulty": "Easy",
        "type": "single response",
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
        "type": "free response",
        "context": "We have found that an attacker with IP address: 72.43.121.44 reading emails using Microsoft Graph API.",
        "question": "Which technique did this attacker used to gain initial access to the tenant?",
        "answer": "password spray attack",

        "solution": "1.From the same IP address, there are several attempted logins ins with different usernames but failed.\n2. The attacker used password spray attack to gain access to the tenant.",

        "start_node": "3",
        "end_node": "7",
        "hop": "2",
    },


    {
        "difficulty": "Medium",
        "type": "general response",
        "context": "We have found that a suspicious client application with name `ReadEmailEWS` is reading emails using Microsoft Graph API.",
        "question": "What other suspicious activity was performed by the same client application?",
        "answer": "Enumerate users and applications with Graph API",

        "solution": "We look through different logs and find that this client application is also used to enumerate all users and applications with Graph API.",

        "start_node": "3",
        "end_node": "8",
        "hop": "1",
    },
    # ------------------------------------------start at 4, 5
    
    {
        "difficulty": "Easy",
        "type": "single response",
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
        "type": "free response",
        "context": "",
        "question": "Is there any suspicious login activity from the IP address `72.43.121.44`? What is it?",
        "answer": "Yes, password spray attack.",
        "solution": "Yes, the same IP address has attempted to log in with different usernames. It is likely a password spray attack.",
        "start_node": "5",
        "end_node": "6",
        "hop": "1",
    },

    # ------------------------------------------start at 8

    {
        "difficulty": "Easy",
        "type": "single response",

        "context": "A client app is using Microsoft Graph API to enumerate users and applications.",
        "question": "what is the ID of the client application that is used to access the Microsoft Graph API?",
        "answer": "bb77fe0b-52af-4f26-9bc7-19aa48854ebf",

        "start_node": "8",
        "end_node": "2",
        "hop": "1",
    },

    {
        "difficulty": "Medium",
        "type": "single response",

        "context": "A client app is using Microsoft Graph API to enumerate users and applications.",
        "question": "On which city is this client application authenticated?",
        "answer": "Dublin",
        "solution": "1. The email is read by client application with id: `bb77fe0b-52af-4f26-9bc7-19aa48854ebf`. \n2. This client application is authenticated in Dublin.",

        "start_node": "8",
        "end_node": "3",
        "hop": "2",
    },

    {
        "difficulty": "Medium",
        "type": "single response",

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
        "type": "single response",

        "context": "A client app is using Microsoft Graph API to enumerate users and applications.",
        "question": "what is the IP address of the user that is used to perform this activity?",
        "answer": "72.43.121.44",
        "solution": "1. The activity is performed by user `mvelazco@DefenderATEVET17.onmicrosoft.com`.\n2. This ID is logged in with IP address: 72.43.121.44.",

        "start_node": "1",
        "end_node": "5",
        "hop": "3",

        "comment": "TODO: The user info is not in the graph yet."
    },

    {
        "difficulty": "Hard",
        "type": "free response",
        "context": "A client app is using Microsoft Graph API to enumerate users and applications.",
        "question": "When did the user gain access to the client app?",
        "solution": "1. The enumeration is performed by the app with the client application ID: `bb77fe0b-52af-4f26-9bc7-19aa48854ebf`. \n2. This ID is the client application `ReadEmailEWS`. \n3. A credential was added to this client application at <TIME>",
        "start_node": "8",
        "end_node": "6",
        "hop": "4",
    },

    {
        "difficulty": "Hard",
        "type": "free response",
        "context": "We have found an attacker enumerating users and applications with a client application.",
        "question": "Which technique did this attacker used to gain initial access to the tenant?",
        "answer": "password spray attack",

        "solution": "1. The activity is performed by user `mvelazco@DefenderATEVET17.onmicrosoft.com`.\n2. This ID is logged in with IP address: 72.43.121.44. \n3.From the same IP address, there are several attempted logins ins with different usernames but failed.\n 4. The attacker used password spray attack to gain access to the tenant.",

        "start_node": "8",
        "end_node": "7",
        "hop": "4",
    },


    {
        "difficulty": "Hard",
        "type": "general response",
        "context": "We have found an attacker enumerating users and applications with a client application.",
        "question": "What other suspicious activity was performed by the same client application?",
        "answer": "Enumerate users and applications with Graph API",

        "solution": "1.The enumeration is performed by the app with the client application ID: `bb77fe0b-52af-4f26-9bc7-19aa48854ebf`. \n2. We look through different logs and find that this client application is also used to read emails with Graph API.",

        "start_node": "8",
        "end_node": "1",
        "hop": "2",
    },
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
#         "type": "single response"

#         "context": "",
#         "question": "Check if there is one IP address that failed to authenticate with multiple accounts.",
#         "answer": "Yes. 72.43.121.44",
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