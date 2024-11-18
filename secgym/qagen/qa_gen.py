from secgym.utils import LLM_call
import json
import pandas as pd
from secgym.qagen.alert_graph import AlertGraph
import argparse
from secgym.utils import process_entity_identifiers
from secgym.qagen.qa_gen_prompts import REWRITE_PROMPT, SOLUTIN_GEN_PROMPT, QAGEN_PROMPT_NO_ENTRY, QAGEN_PROMPT_WITH_ENTRY

class QAGen:
    def __init__(self,
                 qa_path: str,
                 graph_path: str,
                 config_list: list,
                 cache_seed: int,
                 trial: int = 5,
                 include_entry: bool = False
                ) -> None:
        self.qa_path = qa_path
        self.cache_seed = cache_seed
        self.graph_path = graph_path
        self.config_list = config_list
        self.include_entry = include_entry

        self.alert_graph = AlertGraph()
        self.alert_graph.load_graph_from_graphml(self.graph_path)
        print("Alert graph loaded.")
        self.all_paths = self.alert_graph.get_alert_paths()
        
        self.all_questions = []
        self.trial = trial  
        self.accum_cost = 0

    def format_alert_entity_str(self, alert_node: int, entities:list):
        entity_str = ""
        for n in entities:
            entity = self.alert_graph.get_node(n)
            entity_str += f"Type: {entity['node_type']}, Field: {entity['identifier_fields']}, Value: `{entity['value']}`\n"
        return self.get_alert_str(alert_node) + f"Entities from this alert:\n{entity_str.strip()}\n"
    
    def get_alert_str(self, alert_node):
        alert = json.loads(self.alert_graph.get_node(alert_node)['entry'])
        return f"""Time: {alert['TimeGenerated']}
Name: {alert['AlertName']}
Description: {alert['Description']}
"""
    
    def get_entity_str(self, entities, omit_value=False):
        if isinstance(entities, int):
            entities = [entities]
        entity_str = ""
        for n in entities:
            entity = self.alert_graph.get_node(n) 
            entity_str += f"Type: {entity['node_type']}, Field: {entity['identifier_fields']}, Value: "
            if not omit_value:
                entity_str += f"`{entity['value']}`\n"
            else:
                entity_str += f"`???`\n"
        return entity_str

    def get_all_entity_from_alert(self, alert_node):
        alert = json.loads(self.alert_graph.get_node(alert_node)['entry'])
        entities = process_entity_identifiers(alert['Entities'])
        entity_str = ""
        for entity in entities:
            entity_str += f"Type: {entity[0]}, Field: {entity[1]}, Value: `{entity[2]}`\n"
        return entity_str
    
    def qagen_prompt_format(self, path_dict, include_entry=None):
        if include_entry is None:
            include_entry = self.include_entry
            
        compelte_solution_path = path_dict['shortest_alert_path'] + path_dict['end_entities']
        assert len(compelte_solution_path) % 2 == 0
        prompt = "Start Entity:\n" + self.get_entity_str(path_dict['start_entities']) + "\n"
        for i in range(0, len(compelte_solution_path), 2):
            if i == 0:
                prompt += "Start Alert:\n"
            elif i+2 < len(compelte_solution_path):
                prompt += "\nNext Alert:\n"
            else:
                prompt += "\nEnd Alert:\n"
            # print(self.get_all_entity_from_alert(compelte_solution_path[i]))
            prompt += self.get_alert_str(compelte_solution_path[i])
            if include_entry:
                # prompt += "All entities from this alert:\n" + self.get_all_entity_from_alert(compelte_solution_path[i])
                prompt += "Full Alert Entry: " + self.alert_graph.get_node(compelte_solution_path[i])['entry'] + "\n"
            prompt += "\n"
            if i+2 >= len(compelte_solution_path):
                prompt += "End Entity:\n" + self.get_entity_str(path_dict['end_entities'])
            else:
                if include_entry:
                    prompt += "Connected Entities:\n" + self.get_entity_str(compelte_solution_path[i+1])
                else:
                    prompt += "Connected Entities:\n" + self.get_entity_str(compelte_solution_path[i+1], omit_value=True)
        return prompt
    

#     def alert_with_entry(self, alert_node: int, entities:list):
#             alert = json.loads(self.alert_graph.get_node(alert_node)['entry'])
#             entity_str = ""
#             #TODO:changing to read all entities instead of provided ones
#             for n in entities:
#                 entity = self.alert_graph.get_node(n)
#                 entity_str += f"Type: {entity['node_type']}, Field: {entity['identifier_fields']}, Value: `{entity['value']}`\n"
#             return f"""Time: {alert['TimeGenerated']}
# Name: {alert['AlertName']}
# Description: {alert['Description']}
# Full Alert Entry: {alert}
# Entities from this alert that are part of the alert-entity path used to generate the question:
# {entity_str.strip()}
# """
#             #TODO: Add relevent fields from the alert
#             #TODO: How entities are connected to the alert, edge information
#             #Full Alert Entry: {alert}

#     def qagen_prompt_with_entry(self, path_dict):
#         compelte_solution_path = path_dict['shortest_alert_path'] + path_dict['end_entities']
#         assert len(compelte_solution_path) % 2 == 0
#         for i in range(0, len(compelte_solution_path), 2):
#             if i == 0:
#                 entity_str = "Start Alert:\n"
#             elif i+2 < len(compelte_solution_path):
#                 entity_str += "\n, Next Alert:\n"
#             else:
#                 entity_str += "\nEnd Alert:\n"
#             entity_str += self.alert_with_entry(compelte_solution_path[i], [compelte_solution_path[i+1]])
#         return entity_str
    
    def solution_prompt_format(self, path_dict):
        compelte_solution_path = path_dict['shortest_alert_path'] + path_dict['end_entities']
        assert len(compelte_solution_path) % 2 == 0
        entity_str = ""
        for i in range(0, len(compelte_solution_path), 2):
            entity_str += self.format_alert_entity_str(compelte_solution_path[i], [compelte_solution_path[i+1]])
            entity_str += "\n"

        return f"Solution path:\n{entity_str}"
     
    @staticmethod
    def validate_qa_dict(generated_qa: dict):
        required_fields = ["context", "question", "answer"]
        # check every required field is present & no other fields are present
        return len(generated_qa) == len(required_fields) and all([field in generated_qa for field in required_fields]) 


    def generate_qa(self):
        for i, path_dict in enumerate(self.all_paths):
            print(f"Generating {i+1} th question, cost so far: {self.accum_cost}")
            print(path_dict)
            # Construct the prompt
            final_str = self.qagen_prompt_format(path_dict)
            final_str += "\n##############\nYour response:\n"

            print("-" * 10, "Input Prompt", "-" * 10)
            print(final_str)

            print("-" * 10, "Response from LLM", "-" * 10)
            # print(self.solution_prompt_format(path_dict))
            if i > 3:
                exit()
            else:
                continue
            # continue
            response_data = {}
            # Generate QA, try 5 times
            for j in range(self.trial):
                if self.include_entry:
                    prompt = QAGEN_PROMPT_WITH_ENTRY
                else:
                    prompt = QAGEN_PROMPT_NO_ENTRY
                response, cost = LLM_call(
                    instruction=prompt,
                    task=final_str,
                    config_list=self.config_list,
                    response_format={"type": "json_object"},
                    cache_seed=self.cache_seed+j,
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
            for j in range(self.trial):
                response, cost = LLM_call(
                    instruction=SOLUTIN_GEN_PROMPT,
                    task=self.solution_prompt_format(path_dict),
                    config_list=self.config_list,
                    response_format={"type": "json_object"},
                    cache_seed=self.cache_seed+j,
                    return_cost=True
                )
                self.accum_cost += cost
                try:
                    solution_path = json.loads(response)
                    response_data.update(solution_path)
                except json.JSONDecodeError:
                    print("JSON Decoding Error from solution generation:\n", response)
                    continue
                break
                
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
        cache_seed=args.cache_seed,
        include_entry=True
    )

    qagenena.generate_qa()