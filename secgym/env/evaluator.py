from autogen import OpenAIWrapper
import json
import os
import re
from secgym.myconfig import config_list_4o
from secgym.utils import msging, get_full_question

from textwrap import dedent
CHECK_ANSWER_PROMPT = dedent("""Given a golden answer and a submitted answer, please evaluate whether the submitted answer matches the golden answer without ambiguity.

If the submitted answer is an enumeration of information containing the golden answer, it should be considered as false. For example, if the question ask about an IP address and the submitted answer enumerates all the IP addresses in the database.

You are given:
- A question
- The golden answer
- The submitted answer
                        
Only return "True" or "False".
""" 
)

CHECK_SOLUTION_PROMPT = dedent("""Given a question and a ground truth solutionm, please evaluate a given solution based on the ground truth solution.

The ground truth solution contains several steps. Please check if the given solution contain any of the steps in the ground truth solution.

Your response should be in JSON format:
{{
    "<step_i>" : "<"True" or "False">,
    ...
}}
""")


EVAL_ANSWER_TEMPLATE = dedent("""Question: {question}
Golden Answer: {golden_answer}
Submitted Answer: {submitted_answer}""")

EVAL_SOLUTION_TEMPLATE = dedent("""Question: {question}
Golden Solution: {golden_solution}
Submitted Answer: {submitted_answer}""")



class Evaluator:

    def __init__(self,
                 config_list,
                 cache_seed: int = 41,
                 ) -> None:
        self.client = OpenAIWrapper(
            config_list=config_list,
            cache_seed=cache_seed
            )
        self.use_llm = True

    def checking(self, 
                 question: dict, 
                 submitted_answer: str, 
                 eval_step: bool = False
                 ) -> float:
            
            is_correct = self.check_single_response(question, submitted_answer)
            if is_correct == 1:
                return 1
            if "solution" not in question or not eval_step:
                return 0
            
            # check process if solution is provided
            messages=[
                msging(CHECK_SOLUTION_PROMPT, role="system"), 
                msging(EVAL_SOLUTION_TEMPLATE.format(question=get_full_question(question), golden_solution=question["solution"], submitted_answer=submitted_answer), role="user")
            ]
            # print(f"Question: {question.get('context', '')} {question['question']}\n")

            response = self.client.create(messages=messages, response_format= { "type": "json_object" })
            response = response.choices[0].message.content
            
            print("Ground Truth Solution:")
            for k in question["solution"]:
                print(k)
            print(f"-----> Solution Evaluation Result:\n {response}\n--------------------")
            try:
                response = json.loads(response)
            except Exception as e:
                if "json" in str(e):
                    response = response.split("```json")[1].split("```")[0]
                    response = json.loads(response)
                else:
                    print("Error:", e)
                    return 0
            
            discount_factor = 0.4
            # reverse the response
            current_score = 1
            total_score = 0

            step_eval = list(response.values())
            step_eval.reverse()
            for b in step_eval:
                if b == "True":
                    total_score += current_score
                if total_score == 1:
                    return 1
                current_score *= discount_factor

            # 1 2 3 4
            # False  False False True -> 1
            # False False True  False -> 0.3
            # True True True False -> 0.3     # 0.3 + 0.09 + 0.027 = 0.417
            # all false
            return total_score

    def check_single_response(self, question: dict, submitted_answer: str):
        response = self.client.create(messages=[
            msging(CHECK_ANSWER_PROMPT, role="system"), 
            msging(EVAL_ANSWER_TEMPLATE.format(question=get_full_question(question), golden_answer=question["answer"], submitted_answer=submitted_answer), role="user")
        ])
        response = response.choices[0].message.content
        print("Ground Truth Answer:", question["answer"])
        print(f"-----> Answer Evaluation Result: {response}")
        if response == "True":
            return 1
        return 0
        
        
# def criteria_creator(question: dict):
#     if "answer" not in question:
#         print("Warning: No answer in the question. Skipping...")
#         return None
#     if "key_terms" in question:
#         print(f"Warning, Key terms found in question. Skipping...")
#         return None
    
#     client = OpenAIWrapper(config_list=config_list_4o,
#                         response_format= { "type": "json_object" })

#     print(f"Question: {question.get('context', '')} {question['question']}")

#     messages=[
#         msging(CREATOR_PROMPT, role="system"), 
#         msging(f"Question: {question.get('context', '')} {question['question']}\nGolden Answer: {question['answer']}\nYour response:", role="user")
#     ]
#     response = client.create(messages=messages)
#     response = response.choices[0].message.content
#     response = json.loads(response)
#     return response



# if __name__ == '__main__':
#     print('***** Run Evaluator *****')
#     curr_path = os.path.dirname(__file__)
#     qa_path = os.path.join(curr_path, "../env/questions/aad_comprise_qa.json")
#     with open(qa_path, "r") as f:
#         qas = json.load(f)
#     for q in qas:
#         if q['type'] == "single response":
#             continue
#         criteria = criteria_creator(q)
#         if criteria:
#             print(criteria)
#             q.update(criteria)
#         print("=="*50)

#     with open(qa_path, "w") as f:
#         json.dump(qas, f, indent=4)