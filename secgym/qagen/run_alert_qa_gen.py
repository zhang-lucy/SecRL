from secgym.utils import LLM_call
import json
import pandas as pd
from secgym.qagen.alert_paser import processs_incidents
from secgym.qagen.alert_graph import AlertGraph


def qagen_prompt_format(alert_graph, path_dict):
    def format_alert_str(alert_node: int, entities:list):
        alert = json.loads(alert_graph.get_node(alert_node)['entry'])
        entity_str = ""
        for n in entities:
            entity = alert_graph.get_node(n)
            entity_str += f"Type: {entity['node_type']}, Field: {entity['identifier_fields']}, Value: `{entity['value']}`\n"
        return f"""Time: {alert['TimeGenerated [UTC]']}
Name: {alert['AlertName']}
Description: {alert['Description']}
Entities from this alert:
{entity_str.strip()}
"""
    start_alert_str = format_alert_str(path_dict['start_alert'], path_dict['start_entities'])
    end_alert_str = format_alert_str(path_dict['end_alert'], path_dict['end_entities'])

    return f"Start Alert:\n{start_alert_str}\nEnd Alert:\n{end_alert_str}"

# print(qagen_prompt_format(alert_graph, all_paths[0]))
def get_solution_path(alert_graph, path_dict):
    solution = []
    for n in path_dict["shortest_alert_path"]:
        node = alert_graph.get_node(n)
        if node["node_type"] == "entity":
            solution.append(f"Entity field: {node['identifier_fields']}, Value: `{node['value']}`\n")
            

QAGEN_PROMPT = """Your goal is to ask a security question from the given data from a security analyst's perspective.
You are given the start alert and end alert, and corresponding entities. The two alerts are connected by a alert-entity path. The start and end alert might be the same.
You will use the start alert as the context, and ask a question about the entities in the end alert.

The JSON must have the following fields:
- "question": the question about the end alert. The question should be carefully crafted so that:
    1. The question should be natural and relevant to the context, and it should be clear and have a deterministic answer.
    2. But it should not leak the answer. If the start and end alert are the same, you should be more careful since the given entities may have overlapping information.
    3. The question should be specific of the answer you are looking for, and the answer should match the question.
- "answer": the answer to the question. You may be given one or more entities from the end alert, select the most meaningful entity and make sure it is not leaked in the context or question.
- "context": the context from the start alert. you should combine the alert and the entities given in a consistent sentence. You can simplify the context a bit if it is too long. Make sure the answer is not leaked in the context. If the start alert or the related entities contains the answer, you should remove it from the context.

Examples:
##############
Start Alert:
Time: 8/14/2024, 10:34:41.578 PM
Name: Ntdsutil collecting Active Directory information
Description: Attackers might be using Ntdsutil to gather information for persistence or to move laterally in a network or organization. Ntdsutil is a command line tool that provides management facilities for Active Directory Domain Services (AD DS) and Active Directory Lightweight Directory Services (AD LDS). It was launched to maintain the database of AD DS.
Entities from this alert:
Type: process, Field: ExtractedFileName, Value: `powershell.exe`
Type: host, Field: HostName, Value: `vnevado-dc`

End Alert:
Time: 8/14/2024, 10:34:41.578 PM
Name: Ntdsutil collecting Active Directory information
Description: Attackers might be using Ntdsutil to gather information for persistence or to move laterally in a network or organization. Ntdsutil is a command line tool that provides management facilities for Active Directory Domain Services (AD DS) and Active Directory Lightweight Directory Services (AD LDS). It was launched to maintain the database of AD DS.
Entities from this alert:
Type: process, Field: ProcessId__CreatedTimeUtc__CommandLine, Value: `2556__2024-08-01t12:37:29.6522416z__"powershell.exe" -encodedcommand iabuahqazabz...`
##############
Your response:
{
    "context": "A file `powershell.exe` was launched on host `vnevado-dc`, which might be an indicator of an attacker using Ntdsutil to gather information for persistence or to move laterally in a network or organization. Note: Ntdsutil is a command line tool that provides management facilities for Active Directory Domain Services (AD DS) and Active Directory Lightweight Directory Services (AD LDS). It was launched to maintain the database of AD DS.",
    "question": "When was the last time the file `powershell.exe` was launched on host `vnevado-dc`, and what was the process ID?",
    "answer": "Time: 2024-08-01t12:37:29.6522416, Process Id: 2556"
}
##############
##############
Start Alert:
Time: 8/14/2024, 10:34:41.429 PM
Name: Suspicious credential dump from NTDS.dit
Description: Attackers dump NTDS.dit in order to obtain user's credentials which are stored in the domain controller.
Entities from this alert:
Type: process, Field: ProcessId__CreatedTimeUtc__CommandLine, Value: `6748__2024-08-01t12:37:30.2769191z__"ntdsutil.exe" "ac i ntds" ifm "create full c:\temp" q q`
Type: process, Field: ExtractedFileName, Value: `ntdsutil.exe`

End Alert:
Time: 8/14/2024, 10:37:13.064 PM
Name: Suspicious Azure Resource Management activities by a risky user
Description: Suspicious cloud Azure Resource Management (ARM) activities were performed by a user account that signed in to a risky session. This alert was triggered based on a Microsoft Defender for Cloud alert related to ARM and Microsoft Entra ID Protection risk scores.
Entities from this alert:
Type: account, Field: Email, Value: `Megan Bower@vnevado.alpineskihouse.co`
##############
Your response:
{
    "context": "A file `ntdsutil.exe` was launched with this command line: `ntdsutil.exe ac i ntds ifm create full c:\temp q q`. The Process ID was 6748. This process might be an indicator of an attacker dumping NTDS.dit in order to obtain user's credentials which are stored in the domain controller.",
    "question: "Related to this alert, there is also a suspicious Azure Resource Management (ARM) activities, which is likely from the same user. Can you get the email of the user who performed the suspicious ARM activities?",
    "answer": "Megan Bower@vnevado.alpineskihouse.co",
}
##############
##############
Start Alert:
Time: 8/14/2024, 10:37:13.079 PM
Name: Malicious URL was clicked on that device
Description: Malicious URL was clicked on that device
Entities from this alert:
Type: url, Field: Url, Value: `https://dj01161621.bravesand-e1ccd718.eastus.azurecontainerapps.io/`
Type: process, Field: ProcessId__CreatedTimeUtc__CommandLine, Value: `4256__2024-08-01t13:42:52.04__"msedge.exe" --type=utility --utility-sub-type=network.mojom.networkservice --lang=en-us --service-sandbox-type=none --field-trial-handle=1912,i,9358546549091360037,1317674413260171076,262144 --variations-seed-version --mojo-platform-channel-handle=3124 /prefetch:11`

End Alert:
Time: 8/14/2024, 10:34:41.429 PM
Name: Suspicious credential dump from NTDS.dit
Description: Attackers dump NTDS.dit in order to obtain user's credentials which are stored in the domain controller.
Entities from this alert:
Type: process, Field: ExtractedFileName, Value: `ntdsutil.exe`
##############
Your response:
{
    "context": "A malicious URL `https://dj01161621.bravesand-e1ccd718.eastus.azurecontainerapps.io/` was clicked on Microsoft Edge browser, the ProcessId__CreatedTimeUtc__CommandLine is `4256__2024-08-01t13:42:52.04__"msedge.exe" --type=utility --utility-sub-type=network.mojom.networkservice --lang=en-us --service-sandbox-type=none --field-trial-handle=1912,i,9358546549091360037,1317674413260171076,262144 --variations-seed-version --mojo-platform-channel-handle=3124 /prefetch:11`.",
    "question": "Related to this alert, there is also a suspicious credential dump from NTDS.dit. Can you get the file name of the process that was used to dump the NTDS.dit?",
    "answer": "ntdsutil.exe",
}
##############
"""

REWRITE_PROMPT = """Your goal is to rewrite a given context, question, and answer to make sure the answer is not leaked in the context or question.
The question is contructed from a security analyst's perspective from a security alert graph.
You will also be given the start alert and end alert, and corresponding entities that was used to generate question.
The two alerts are connected by a alert-entity path. The start and end alert might be the same.
Your response should be in JSON format containing 3 fields: "context", "question", and "answer".
"""


def validate_qa_dict(generated_qa: dict):
    required_fields = ["context", "question", "answer"]

    # check every required field is present & no other fields are present
    return len(generated_qa) == len(required_fields) and all([field in generated_qa for field in required_fields]) 


# with open(qa_path, "r") as f:
#     all_questions = json.load(f)
# for question in all_questions:
#     final_str = qagen_prompt_format(alert_graph, question)
#     if question['answer'] in question['question'] or question['answer'] in question['context']:
#         print(f"Original prompt: {final_str}")
#         print(f"context: {question['context']}")
#         print(f"Original question: {question['question']}")
#         print(f"Original answer: {question['answer']}")
#         print("-"*50)

from secgym.myconfig import config_list_4o
# ---------

# params 
qa_path = "newqa.json"
cache_seed = 41

alert_graph = AlertGraph()
alert_graph.load_graph_from_graphml("sample_incident.graphml")
print("Alert graph loaded.")
all_paths = alert_graph.get_alert_paths()

all_questions = []
for i, path_dict in enumerate(all_paths):
    print(f"Generating {i+1} th question.")
    final_str = qagen_prompt_format(alert_graph, path_dict)
    final_str += "\n##############\nYour response:\n"
    print(final_str)
    for i in range(5):
        response = LLM_call(
            instruction=QAGEN_PROMPT,
            task=final_str,
            config_list=config_list_4o,
            response_format={"type": "json_object"},
            cache_seed=cache_seed+i
        )

        response_data = json.loads(response)
        if validate_qa_dict(response_data):
            print(response)
            break
        else:
            print("Invalid response\n", response)
            response_data = {}
    print("-"*100)
    print("-"*100)

    if response_data['answer'] in response_data['question'] or response_data['answer'] in response_data['context']:
        response = LLM_call(
            instruction=REWRITE_PROMPT,
            task=final_str + "\nQuestion: \n" + json.dumps(response_data),
            config_list=config_list_4o,
            response_format={"type": "json_object"},
            cache_seed=cache_seed
        )
        response_data = json.loads(response)
        if not validate_qa_dict(response_data):
            print("Invalid response from rewrite. continue.\n", response)
            response_data = {}    
    
    response_data.update(path_dict)
    all_questions.append(response_data)
    with open(qa_path, "w") as f:
        json.dump(all_questions, f, indent=4)


