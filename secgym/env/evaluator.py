from autogen import OpenAIWrapper
import json
import os
from secgym.myconfig import config_list_4o
from secgym.env.prompts import CREATOR_PROMPT, CHECKER_PROMPT

def msging(msg: str, role: str="user"):
    return {"role": role, "content": msg}


def to_abs_path(relative_path):
    return os.path.join(os.path.dirname(__file__), relative_path)


class Evaluator:

    def __init__(self,
                 config_list,
                 ) -> None:
        self.client = OpenAIWrapper(config_list=config_list)

    def string_matching():
        pass

    def checking(self, 
                 question: dict, 
                 submitted_answer: str, 
                 use_llm: bool = True,
                 config_list: dict = None,
                 ):
        if not use_llm:
            match_count = 0
            for key_term in question["key_terms"]:
                if key_term.lower() in submitted_answer.lower():
                    match_count += 1
            return match_count/len(question["key_terms"])
        else:
            if not config_list:
                raise ValueError("config_list is required when use_llm is True")
            
            

            messages=[msging(CHECKER_PROMPT, role="system"), 
                    msging(f"Question: {question.get('context', '')} {question['question']}\nGolden Answer: {question['answer']}\nYour response: {submitted_answer}", role="user")]
            # print(f"Question: {question.get('context', '')} {question['question']}\n")
            response = self.client.create(messages=messages, response_format= { "type": "json_object" })
            response = response.choices[0].message.content
            response = json.loads(response)
            return response["score"]
    
    def check_single_response(self, question: dict, submitted_answer: str):

        pass
        

    
def criteria_creator(question: dict):
    if "answer" not in question:
        print("Warning: No answer in the question. Skipping...")
        return None
    if "key_terms" in question:
        print(f"Warning, Key terms found in question. Skipping...")
        return None
    
    client = OpenAIWrapper(config_list=config_list_4o,
                        response_format= { "type": "json_object" })

    print(f"Question: {question.get('context', '')} {question['question']}")

    messages=[
        msging(CREATOR_PROMPT, role="system"), 
        msging(f"Question: {question.get('context', '')} {question['question']}\nGolden Answer: {question['answer']}\nYour response:", role="user")
    ]
    response = client.create(messages=messages)
    response = response.choices[0].message.content
    response = json.loads(response)
    return response



if __name__ == '__main__':
    print('***** Run Evaluator *****')
    qa_path = to_abs_path("../env/questions/aad_comprise_qa.json")
    with open(qa_path, "r") as f:
        qas = json.load(f)
    for q in qas:
        if q['type'] == "single response":
            continue
        criteria = criteria_creator(q)
        if criteria:
            print(criteria)
            q.update(criteria)
        print("=="*50)

    with open(qa_path, "w") as f:
        json.dump(qas, f, indent=4)