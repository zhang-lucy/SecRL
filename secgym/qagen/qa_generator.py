from secgym.utils import LLM_call
from textwrap import dedent
import networkx as nx
import json
import os

QAGEN_PROMPT = """Given an investigation path, please generate a list of questions from it.
The path is consists of a series of nodes with two types: Investigation and IoC. 
- Investigation node: It is an query to one or more tables in the data to find relevant information.
- IoC node: It is an indicator of compromise that is found during the investigation. It could be a definition of a suspicious activity or a specific entity that is involved in the incident.

The starting node and ending node are always IoC nodes. You will be given one path, and a list of (start, end) tuples that you need to generate questions for.

You reply should be in JSON format. The key would be the question number, and the value would be a JSON object with the following fields:
The JSON should have the following fields:
- "difficulty": the difficulty level of the question. It can be "Easy", "Medium", or "Hard". Usually, the difficulty level is determined by the number of hops, but this might not always be the case.
- "context": the context from the starting node. 
- "question": the question to be asked to the user. The question should be carefully crafted so that:
    1. The question should be clear and have a deterministic answer.
    2. The question should ask about the final node in the path, but it SHOULD NOT leak any information from the final node and intermediate nodes.
    3. It should not leak information about the table's names. The questions should be generic, for example, "what client app is authenticating instead of what 'service principal' is authenticating".
- "answer": the answer to the question, should be a single element, such as an IP address, a user name, etc.
- "solution": Optional. A list of strings. The solution should be a step-by-step guide to find the answer. Each step should base on an IoC node (not an investigation node), and it is also based on a key information found in the previous step (previous ioc node). You may don't need this field for single hop questions.
- "tables": A list of tables that are queried in the investigation path, if any.
- "start_node" and "end_node": the node id of the start and end node respectively.
- "hop": number of tables to be queried to find the answer.

Speical Note: Sometimes it doesn't make sense to ask a question about two selected nodes. In that case, you should still try to generate the question, but add an addition field "Need Review" : True to that question.


Example
######################
Investigation
######################
Path: 1->2->3->7->8->9->10
Required questions: [(1, 3), (1, 8), (1, 10)]
#ID: 1
#Type: IOC
#Description: There is a suspicious email reading event, where the emails are read with Graph API through a previously unknown application registration.

#ID: 2
#Type: Investigation
#Description: Check table `OfficeActivity` with Graph API's id for mail read events.
#Table: OfficeActivity

#ID: 3
#Type: IOC
#Description: ClientAppId: bb77fe0b-52af-4f26-9bc7-19aa48854ebf

#ID: 7
#Type: Investigation
#Description: Check `AADServicePrincipalSignInLogs` to identify the last time this client app with `ClientAppId` was authenticated.
#Table: AADServicePrincipalSignInLogs

#ID: 8
#Type: IOC
#Description: IPAddress: 72.43.121.34
#AdditionalInfo: The IP Address where the service principal authenticated from.

#ID: 9
#Type: Investigation
#Description: Check `SigninLogs` for other authentication events from the same IP address.
#Table: SigninLogs

#ID: 10
#Type: IOC
#Description: Multiple users are authenticating from the same IP address but failed. There is one account that successfully authenticated from this account: mvelazco@defenderATEVET17@onmicrosoft.com. This could be a password spraying attack.

######################
Your Response
######################
{
    "q1": {
        "difficulty": "Easy",
        "context": "There is a suspicious email reading event, where the emails are read with Graph API through a previously unknown application registration.",
        "question": "what is the ID of the client application?",
        "answer": "bb77fe0b-52af-4f26-9bc7-19aa48854ebf",
        "tables": ["OfficeActivity"],
        "start_node": "1",
        "end_node": "3",
        "hop": "1"
    },
    "q2": {
        "difficulty": "Medium",
        "context": "There is a suspicious email reading event, where the emails are read with Graph API through a previously unknown application registration.",
        "question": "what is the IP address of the user that is used to perform this email reading activity?",
        "answer": "72.43.121.44",
        "solution": [
            "1. The email is read by client application with ID: bb77fe0b-52af-4f26-9bc7-19aa48854ebf.",
            "2. This ID is logged in with IP address: 72.43.121.44."
        ],
        "tables": ["OfficeActivity", "AADServicePrincipalSignInLogs"],
        "start_node": "1",
        "end_node": "8",
        "hop": "2",
    },
    "q3": {
        "difficulty": "Hard",
        "context": "There is a suspicious email reading event, where the emails are read with Graph API through a previously unknown application registration.",
        "question": "Which technique did this attacker used to gain initial access to the tenant?"
        "answer": "Password Spray",
        "solution": [
            "1. The email is read by client application with ID: bb77fe0b-52af-4f26-9bc7-19aa48854ebf.",
            "2. This ID is logged in with IP address: 72.43.121.44.",
            "3. Multiple users are authenticating from the same IP address but failed. There is one account that successfully authenticated from this account: mvelazco@defenderatevet17.onmicrosoft.com. This could be a password spraying attack.",
        ],
        "tables": ["OfficeActivity", "AADServicePrincipalSignInLogs", "SigninLogs"],
        "start_node": "1",
        "end_node": "10",
        "hop": "3",
    }
}
"""


class QAGenerator:
    def __init__(self, graphml_file, question_file, config_list):
        self.graph = nx.read_graphml(graphml_file)
        self.config_list = config_list
        self.question_file = question_file
        self.generated_pairs = set()
        self.questions_list = []

        if os.path.exists(question_file):
            with open(question_file, 'r') as file:
                self.questions_list = json.load(file)
                for question in self.questions_list:
                    start_node = question.get('start_node')
                    end_node = question.get('end_node')
                    if start_node and end_node:
                        self.generated_pairs.add((start_node, end_node))


    def _get_all_combinations(self, start_node, end_node):
        try:
            path = nx.shortest_path(self.graph, source=start_node, target=end_node)
        except nx.NetworkXNoPath:
            return None, []

        ioc_nodes_in_path = [node for node in path if self.graph.nodes[node].get('type') == 'IoC']

        combinations = [(ioc_nodes_in_path[i], ioc_nodes_in_path[j]) for i in range(len(ioc_nodes_in_path)) for j in range(i + 1, len(ioc_nodes_in_path))]

        return path, combinations

    def _node_to_string(self, node_id):
        node_data = self.graph.nodes[node_id]
        node_type = node_data.get('type', '')
        node_description = node_data.get('description', '')
        table_name = node_data.get('table_name', '')
        additional_info = node_data.get('additional_info', '')

        parts = [f"#ID: {node_id}", f"#Type: {node_type}", f"#Description: {node_description}"]

        if node_type == 'Investigation' and table_name:
            parts.append(f"#Table: {table_name}")

        if additional_info:
            parts.append(f"#AdditionalInfo: {additional_info}")

        return "\n".join(parts)

    def get_leaf_ioc_nodes(self):
        # A leaf node in an undirected graph will have a degree of 1
        return [node for node in self.graph.nodes if self.graph.degree(node) == 1 and self.graph.nodes[node].get('type') == 'IoC']


    def _generate_questions_for_one_path(self, start_node, end_node):
        path, all_combinations = self._get_all_combinations(start_node, end_node)
        filtered_combinations = [pair for pair in all_combinations if pair not in self.generated_pairs]

        print(f"Path: {path}")
        print(f"Filtered Combinations: {filtered_combinations}")
        if not path or len(filtered_combinations) == 0: 
            return []

        for pair in filtered_combinations:
            self.generated_pairs.add(pair)

        node_strings = [self._node_to_string(node) for node in path]
        nodes_str = "\n\n".join(node_strings)

        final_str = (
            f"Required questions: {filtered_combinations}\n"
            f"Path: {'->'.join(map(str, path))}\n"
            f"Nodes:\n{nodes_str}"
        )
        # print(final_str)

        response = LLM_call(
            instruction=QAGEN_PROMPT,
            task=final_str,
            config_list=self.config_list,
            response_format={"type": "json_object"}
        )
        print(response)
        response_data = json.loads(response)

        return response_data.values()

    def generate_questions(self):
        leaf_ioc_nodes = self.get_leaf_ioc_nodes()

        for start_node in leaf_ioc_nodes:
            for end_node in leaf_ioc_nodes:
                if start_node == end_node:
                    continue

                questions = self._generate_questions_for_one_path(start_node, end_node)
                if isinstance(questions, dict):
                    questions = [questions]

                if questions:
                    self.questions_list.extend(questions)

                    # Save the questions to the config file
                    with open(self.question_file, 'w') as file:
                        json.dump(self.questions_list, file, indent=4)

