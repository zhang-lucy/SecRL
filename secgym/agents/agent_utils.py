from autogen import OpenAIWrapper
import re
from secgym.myconfig import config_list_4o, config_list_4_0125, config_list_4_turbo, config_list_35

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
