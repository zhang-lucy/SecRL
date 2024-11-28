from secgym.myconfig import CONFIG_LIST
from secgym.qagen.qa_gen import QAGen
import os
import argparse

def get_args():
    parser = argparse.ArgumentParser(description="Run Alert QA Generation")
    parser.add_argument("--qa_path", "-q", type=str, default="newqa.json", help="Path to save the generated QA")
    parser.add_argument("--graph_path", "-g", type=str, default="sample_incident.graphml", help="Path to the alert graph")
    parser.add_argument("--cache_seed", type=int, default=41, help="Seed for the cache")
    parser.add_argument("--include_entry", action="store_true", help="Include full alert entry in the question prompt")
    parser.add_argument("--model", "-m", type=str, default="gpt-4o", help="Model to use for QA generation")
    parser.add_argument("--solution_model", "-s", type=str, default="gpt-4o", help="Model to use for solution generation")
    parser.add_argument("--include_incident", action="store_false", help="Include incident context in the question prompt")
    args = parser.parse_args()
    return args

args = get_args()
graph_files = [
     #'incident_34.graphml',
     #'incident_166.graphml',
    'incident_55.graphml',
     #'incident_5.graphml',
     #'incident_38.graphml',
     #'incident_134.graphml',
     #'incident_39.graphml',
    'incident_322.graphml'
 ]


# Changes: You can pass in one config list with different models
# BE SURE TO include a "tags": [<model_name>] for each dictionary in the config_list to include the model name
# We will filter out the config list passed in to only include the model that model_name in the tags is equal to qa_gen_model
# config_list = [
#     {
#         "model": "some name",
#         "tags": ["gpt-4o"]
#     },
#     {
#         "model": "some name",
#         "tags": ["gpt-3.5"]
#     }
# ]
# If qa_gen_model = "gpt-4o", the config_list for qa_gen will be only the first dictionary in the config_list


# form question file name
qa_file_suffix = "qa"
if args.include_entry:
    qa_file_suffix += "_entry"
if args.include_incident:
    qa_file_suffix += "_incident"
qa_file_suffix += f"_{args.model}"
if args.solution_model is not None and args.solution_model != args.model:
    qa_file_suffix += f"_{args.solution_model}"
qa_file_suffix += f"_c{args.cache_seed}.json"

for file in graph_files:
    qagenena = QAGen(
        qa_path=f"../env/questions/{file.split('.')[0]}_{qa_file_suffix}",
        graph_path=os.path.join("graph_files", file),
        config_list=CONFIG_LIST,
        qa_gen_model=args.model,
        solution_gen_model=args.solution_model,
        cache_seed=41,
        include_entry=args.include_entry,
        include_incident=args.include_incident,
        max_question_count=100
    )

    # qagenena.generate_qa()
