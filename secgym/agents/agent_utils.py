import re
from secgym.myconfig import config_list_4o, config_list_4_0125, config_list_4_turbo, config_list_35
from autogen import OpenAIWrapper
import time
from typing import List
from openai.types.chat import ChatCompletion


def msging(msg: str, role: str="user"):
    return {"role": role, "content": msg}



def sql_parser(action: str, code_block=False):
    if "submit[" in action:
        pattern = r'submit\[(.*)\]'
        submit = True
    else:
        if code_block:
            pattern = r'```sql(.*?)```'
        pattern = r'execute\[(.*)\]'
        submit = False

    matches = re.findall(pattern, action, re.DOTALL)
    if len(matches) > 0:
        action = matches[0]
        if ";" in action:
            return action[:action.index(";")], True, submit
        return action, True, submit
    return action, False, submit

def call_llm(client:OpenAIWrapper, messages:List[str], retry_num=10, retry_wait_time=5) -> ChatCompletion:
    for _ in range(retry_num):
        try: 
            response = client.create(
                messages=messages,
            )
            break
        except TimeoutError as e:
            time.sleep(retry_wait_time)
    return response