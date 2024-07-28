from autogen import OpenAIWrapper
import re
from secgym.myconfig import config_list_4o, config_list_4_0125, config_list_4_turbo, config_list_35

def msging(msg: str, role: str="user"):
    return {"role": role, "content": msg}

def call_llm(model, messages, temperature=0):
    model_maps = {
        "gpt-35-turbo-0125": config_list_35,
        "gpt-4o": config_list_4o,
        "gpt-4-0125-preview": config_list_4_0125,
        "gpt-4-turbo-2024-04-09": config_list_4_turbo
    }
    client = OpenAIWrapper(config_list=model_maps[model])
    response = client.create(
        messages=messages,
        temperature=temperature,
        cache_seed=41
    )
    return response.choices[0].message.content



def sql_parser(action: str):
    if "submit[" in action:
        pattern = r'submit\[(.*)\]'
        submit = True
    else:
        pattern = r'execute\[(.*)\]'
        submit = False

    matches = re.findall(pattern, action, re.DOTALL)
    if len(matches) > 0:
        action = matches[0]
        if ";" in action:
            return action[:action.index(";")], True, submit
        return action, True, submit
    return action, False, submit
