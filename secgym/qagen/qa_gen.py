from secgym.utils import LLM_call
import json
import pandas as pd
from secgym.qagen.alert_graph import AlertGraph
import argparse

#TODO: tweak prompt
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
Type: process, Field: ProcessId__CreatedTimeUtc__CommandLine, Value: `6748__2024-08-01t12:37:30.2769191z__"ntdsutil.exe" "ac i ntds" ifm "create full c:\\temp" q q`
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

SOLUTIN_GEN_PROMPT = """Given an alert-entity path, please generate a solution path, where the question asks about the end entity.
In each step of the solution path, please make sure you include the entity field and value.

Your response should be in JSON format, containing field "solution" which is a list of strings.

Examples:
##############
##############
Solution path:
Time: 8/14/2024, 10:34:41.578 PM
Name: Ntdsutil collecting Active Directory information
Description: Attackers might be using Ntdsutil to gather information for persistence or to move laterally in a network or organization. Ntdsutil is a command line tool that provides management facilities for Active Directory Domain Services (AD DS) and Active Directory Lightweight Directory Services (AD LDS). It was launched to maintain the database of AD DS.
Entities from this alert:
Type: process, Field: ProcessId__CreatedTimeUtc__CommandLine, Value: `6748__2024-08-01t12:37:30.2769191z__"ntdsutil.exe" "ac i ntds" ifm "create full c:\temp" q q`
##############
Your response:
{
    "solution": [
        "The attacker launched ntdsutil with the command line `ntdsutil.exe ac i ntds ifm create full c:\temp q q`." at `2024-08-01t12:37:30.2769191z`, with Process ID `6748`.
    ]
}
##############
##############
Solution path:
Time: 8/14/2024, 10:34:41.578 PM
Name: Ntdsutil collecting Active Directory information
Description: Attackers might be using Ntdsutil to gather information for persistence or to move laterally in a network or organization. Ntdsutil is a command line tool that provides management facilities for Active Directory Domain Services (AD DS) and Active Directory Lightweight Directory Services (AD LDS). It was launched to maintain the database of AD DS.
Entities from this alert:
Type: host, Field: HostName, Value: `vnevado-dc`

Time: 8/14/2024, 10:37:13.045 PM
Name: Azure Resource Manager operation from suspicious proxy IP address
Description: Microsoft Defender for Resource Manager detected a resource management operation from an IP address that is associated with proxy services, such as TOR. While this behavior can be legitimate, it's often seen in malicious activities, when threat actors try to hide their source IP.
Entities from this alert:
Type: ip, Field: Address, Value: `185.220.101.1`

Time: 8/14/2024, 10:37:13.064 PM
Name: Suspicious Azure Resource Management activities by a risky user
Description: Suspicious cloud Azure Resource Management (ARM) activities were performed by a user account that signed in to a risky session. This alert was triggered based on a Microsoft Defender for Cloud alert related to ARM and Microsoft Entra ID Protection risk scores.
Entities from this alert:
Type: account, Field: AadUserId, Value: `6c16dea3-5326-461e-a48e-38b527df3a70`
##############
Your response:
{
    "solution": [
        "There is a collection of active directory information with ntutil.exe on host `vnevado-dc`.",
        "There is a suspicious Azure Resource Manager operation from a proxy IP address `185.220.101.1`.",
        "There is a suspicious Azure Resource Management activities by a risky user with AadUserId `6c16dea3-5326-461e-a48e-38b527df3a70`."

}
#############
#############
Solution path:
Time: 8/14/2024, 10:37:13.011 PM
Name: Email messages containing malicious URL removed after delivery
Description: Emails with malicious URL that were delivered and later removed -V1.0.0.3
Entities from this alert:
Type: account, Field: Name, Value: `Megan Bower`

Time: 8/14/2024, 10:37:12.993 PM
Name: A potentially malicious URL click was detected
Description: We have detected that one of your users has recently clicked on a link that was found to be malicious. -V1.0.0.5
Entities from this alert:
Type: account, Field: Sid, Value: `S-1-5-21-1840151660-3534030288-105586563-1127`
##############
Your response:
{
    "solution": [
        "The email account `Megan Bower` received an email with a malicious URL.",
        "The user with SID `S-1-5-21-1840151660-3534030288-105586563-1127` clicked on the malicious URL."
    ]
}
"""

class QAGen:
    def __init__(self,
                 qa_path: str,
                 graph_path: str,
                 config_list: list,
                 cache_seed: int,
                 trial: int = 5
                ) -> None:
        self.qa_path = qa_path
        self.cache_seed = cache_seed
        self.graph_path = graph_path
        self.config_list = config_list

        self.alert_graph = AlertGraph()
        self.alert_graph.load_graph_from_graphml(self.graph_path)
        print("Alert graph loaded.")
        self.all_paths = self.alert_graph.get_alert_paths()
        
        self.all_questions = []
        self.trial = trial  
        self.accum_cost = 0

    def format_alert_str(self, alert_node: int, entities:list):
            alert = json.loads(self.alert_graph.get_node(alert_node)['entry'])
            entity_str = ""
            #TODO:changing to read all entities instead of provided ones
            for n in entities:
                entity = self.alert_graph.get_node(n)
                entity_str += f"Type: {entity['node_type']}, Field: {entity['identifier_fields']}, Value: `{entity['value']}, Full Entity Entry: {json.dumps(entity)}`\n"
            return f"""Time: {alert['TimeGenerated']}
                    Name: {alert['AlertName']}
                    Description: {alert['Description']}
                    Full Alert Entry: {alert}
                    Entities from this alert that are part of the alert-entity path used to generate the question:
                    {entity_str.strip()}
                    """
                    #TODO: Add relevent fields from the alert
                    #TODO: How entities are connected to the alert, edge information
                    #Full Alert Entry: {alert}

    def qagen_prompt_format(self, path_dict):
        # start_alert_str = self.format_alert_str(path_dict['start_alert'], path_dict['start_entities'])
        # end_alert_str =  self.format_alert_str(path_dict['end_alert'], path_dict['end_entities'])
        # return f"Start Alert:\n{start_alert_str}\nEnd Alert:\n{end_alert_str}"
        compelte_solution_path = path_dict['shortest_alert_path'] + path_dict['end_entities']
        assert len(compelte_solution_path) % 2 == 0
        for i in range(0, len(compelte_solution_path), 2):
            if i == 0:
                entity_str = "Start Alert:\n"
            elif i+2 < len(compelte_solution_path):
                entity_str += "\n, Next Alert:\n"
            else:
                entity_str += "\nEnd Alert:\n"

            entity_str += self.format_alert_str(compelte_solution_path[i], [compelte_solution_path[i+1]])

        return entity_str

    def solution_prompt_format(self, path_dict):
        compelte_solution_path = path_dict['shortest_alert_path'] + path_dict['end_entities']
        assert len(compelte_solution_path) % 2 == 0
        entity_str = ""
        for i in range(0, len(compelte_solution_path), 2):
            entity_str += self.format_alert_str(compelte_solution_path[i], [compelte_solution_path[i+1]])
            entity_str += "\n"

        return f"Solution path:\n{entity_str}"
     
#     def get_solution_path(self, path_dict):
# #  {'start_alert': 14,
# #   'end_alert': 13,
# #   'start_entities': [15],
# #   'end_entities': [6],
# #   'shortest_alert_path': [14, 1, 13]},
#         solution = []
#         for n in path_dict["shortest_alert_path"]:
#             node = self.alert_graph.get_node(n)
#             if node["node_type"] == "entity":
#                 solution.append(f"Entity field: {node['identifier_fields']}, Value: `{node['value']}`\n")

    @staticmethod
    def validate_qa_dict(generated_qa: dict):
        required_fields = ["context", "question", "answer"]
        # check every required field is present & no other fields are present
        return len(generated_qa) == len(required_fields) and all([field in generated_qa for field in required_fields]) 


    def generate_qa(self):
        for i, path_dict in enumerate(self.all_paths):
            print(f"Generating {i+1} th question, cost so far: {self.accum_cost}")

            # Construct the prompt
            final_str = self.qagen_prompt_format(path_dict)
            final_str += "\n##############\nYour response:\n"

            print("-" * 10, "Input Prompt", "-" * 10)
            print(final_str)


            print("-" * 10, "Response from LLM", "-" * 10)
            response_data = {}
            # Generate QA, try 5 times
            for i in range(self.trial):
                response, cost = LLM_call(
                    instruction=QAGEN_PROMPT,
                    task=final_str,
                    config_list=self.config_list,
                    response_format={"type": "json_object"},
                    cache_seed=self.cache_seed+i,
                    return_cost=True
                )
                self.accum_cost += cost

                print(response)
                try:
                    response_data = json.loads(response)
                except json.JSONDecodeError:
                    print("JSON Decoding Error:\n", response)
                    continue
                
                if not self.validate_qa_dict(response_data):
                    print("Invalid fields in generated question\n", response)
                    continue
    
                # We need to make sure the answer is not leaked in the context or question
                # If the answer is in the context or question, we need to rewrite the context, question, and answer
                if response_data['answer'] in response_data['question'] or response_data['answer'] in response_data['context']:
                    response, cost = LLM_call(
                        instruction=REWRITE_PROMPT,
                        task=final_str + "\nQuestion: \n" + json.dumps(response_data),
                        config_list=self.config_list,
                        response_format={"type": "json_object"},
                        cache_seed=self.cache_seed,
                        return_cost=True
                    )
                    self.accum_cost += cost
                    print("-" * 10, "Rewrite QA", "-" * 10)
                    print(response)
                    try:
                        response_data = json.loads(response)
                    except json.JSONDecodeError:
                        print("JSON Decoding Error from rewrite:\n", response)
                        continue  

                if not self.validate_qa_dict(response_data):
                    print("Invalid fields from rewrite. continue.\n", response)
                    continue

                if not (response_data['answer'] in response_data['question'] or response_data['answer'] in response_data['context']):
                    # double check the answer is not leaked
                    break
                    
            # generate the solution path
            response, cost = LLM_call(
                instruction=SOLUTIN_GEN_PROMPT,
                task=self.solution_prompt_format(path_dict),
                config_list=self.config_list,
                response_format={"type": "json_object"},
                cache_seed=self.cache_seed,
                return_cost=True
            )
            self.accum_cost += cost
            response_data.update(json.loads(response))
            print("-" * 10, "Solution Path", "-" * 10)
            print(response)
            print("-"*100)
            print("-"*100)

            # append the path used to generate the QA
            response_data.update(path_dict)

            # Save the QA
            self.all_questions.append(response_data)
            with open(self.qa_path, "w") as f:
                json.dump(self.all_questions, f, indent=4)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Alert QA Generation")
    parser.add_argument("--qa_path", "-q", type=str, default="newqa.json", help="Path to save the generated QA")
    parser.add_argument("--graph_path", "-g", type=str, default="sample_incident.graphml", help="Path to the alert graph")
    parser.add_argument("--cache_seed", type=int, default=41, help="Seed for the cache")
    args = parser.parse_args()

    from secgym.myconfig import config_list_4o

    qagenena = QAGen(
        qa_path=args.qa_path,
        graph_path=args.graph_path,
        config_list=config_list_4o,
        cache_seed=args.cache_seed
    )

    qagenena.generate_qa()