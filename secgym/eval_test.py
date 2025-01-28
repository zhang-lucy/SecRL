import json
from secgym.env.evaluator import Evaluator
from secgym.myconfig import CONFIG_LIST

import autogen
def filter_config_list(config_list, model_name):
    config_list = autogen.filter_config(config_list, {'tags': [model_name]})
    if len(config_list) == 0:
        raise ValueError(f"model {model_name} not found in the config list, please put 'tags': ['{model_name}'] in the config list to inicate this model")
    return config_list

with open("./env/questions/test/incident_5_qa_incident_gpt-4o_c41.json", "r") as f:
    agent_log = json.load(f)


config_list = filter_config_list(CONFIG_LIST, "gpt-4o")

evaluator = Evaluator(
    config_list=config_list, ans_check_reflection=False, sol_check_reflection=False)


question = agent_log[1]
answer = "vnevado-win11t.vnevado.alpineskihouse.co"
evaluator.checking(question, answer, eval_step=True)