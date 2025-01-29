from autogen import OpenAIWrapper
import json
import os
import re
from secgym.myconfig import config_list_4o
from secgym.utils import msging, get_full_question

from textwrap import dedent
CHECK_ANSWER_PROMPT = dedent("""Given a golden answer to a security question and a submitted answer, please evaluate whether the submitted answer matches the golden answer without ambiguity.

If the submitted answer is an enumeration of information containing the golden answer, it should be considered as false. For example, if the question ask about an IP address and the submitted answer enumerates all the IP addresses in the database.

You are given:
- A question
- The golden answer
- The submitted answer

First give a brief analysis using 1-2 short sentences, then give your decision.
Follow this format:
Analysis: <your analysis>
Decision: <"True" or "False">       
""" 
)

ANSWER_CHECKING_REFLECTION_PROMPT = """Given a golden answer and a submitted answer, please evaluate whether the submitted answer matches the golden answer without ambiguity.
You are given:
- A question
- The golden answer
- The submitted answer
You are also give a previous evaluation of this submitted answer. 
Please serve as a second reviewer to double-check whether the answer is correct.

Reflection: <your reflection>
Decision: <"True" or "False", whether the submitted answer is correct>
"""

EVAL_ANSWER_TEMPLATE = dedent("""Question: {question}
                              
Golden Answer: {golden_answer}
                              
Submitted Answer: {submitted_answer}""")

# ---- Solution Evaluation ----

EVAL_SOLUTION_TEMPLATE = dedent("""Question: {question}
                                
Golden Solution: 
{golden_solution}
                                
Submitted Answer: 
{submitted_answer}""")

CHECK_SOLUTION_PROMPT = """Given a security question and a  truth solution, please evaluate the correctness of the a given answer based on the ground truth solution.ground
The ground truth solution may contain several steps. Please check if the given solution contain any of the steps in the ground truth solution.
Please go through each step in the ground truth solution and evaluate whether the given solution contains the key information (Indicator of comprise) in the step.
Note that the key information should not be the ones that is already present in the question.
         
Your response should be in JSON format:
{
    "<step_i>" : {
            "analysis": "<your analysis>",
            "decision": "<"True" or "False">,
        },
    ...
}
step_i is the step number from the ground truth solution, starting from 0. For each step, you must have `analysis` and `decision` fields.
"""

SOLUTION_CHECKING_REFLECTION_PROMPT = """Given a security question and a  truth solution, please evaluate the correctness of the a given answer based on the ground truth solution.ground
The ground truth solution may contain several steps. Please check if the given solution contain any of the steps in the ground truth solution.
Please go through each step in the ground truth solution and evaluate whether the given solution contains the key information (Indicator of comprise) in the step.
Note that the key information should not be the ones that is already present in the question.

You will also be given a previous evaluation of this solution. Reflect on the previous evaluation and give the final evaluation whether each step in the solution is correct or not.

Your response should be in JSON format:
{
    "<step_i>" : {
            "reflection": "<your reflection>",
            "decision": "<"True" or "False">,
        }
    ...
}
step_i is the step number from the ground truth solution, starting from 0. For each step, you must have `reflection` and `decision` fields.
"""

class Evaluator:

    def __init__(self,
                 config_list,
                 cache_seed: int = 41,
                 ans_check_reflection: bool = False,
                 sol_check_reflection: bool = False
                 ) -> None:
        #print(config_list)
        self.client = OpenAIWrapper(
            config_list=config_list,
            cache_seed=cache_seed
            )
        self.use_llm = True
        self.ans_check_reflection = ans_check_reflection
        self.sol_check_reflection = sol_check_reflection
    
    def _get_json_response(
        self,
        system_prompt,
        task,
    ):
        messages=[
            msging(system_prompt, role="system"), 
            msging(task, role="user")
        ]
        response = self.client.create(messages=messages, response_format= { "type": "json_object" }).choices[0].message.content
        print("\n\n")
        print(response)
        if "```json" in response:
            print("Spearating ```json placeholder")
            response = response.split("```json")[1].split("```")[0]
        try:
            response = json.loads(response)
            return response, True
        except Exception as e:
            print(f"Error: {e}: {response}")
            return response, False
            

    def checking(self, 
                 question: dict, 
                 submitted_answer: str, 
                 eval_step: bool = False
                 ) -> dict:
            
            # 1. Check if the answer is correct
            eval_dict = self.check_single_response(question, submitted_answer)
            if eval_dict["reward"] == 1:
                return eval_dict
            if "solution" not in question or not eval_step:
                if "solution" not in question:
                    print("Warning: No solution in the question. Skipping solution checking...")
                return eval_dict
            
            # 2. Check if the solution is correct
            if isinstance(question["solution"], list):
                golden_solution = ""
                for i, s in enumerate(question["solution"]):
                    golden_solution += f"Step {i}: {s}\n"
            else:
                golden_solution = question["solution"]

            solution_str = EVAL_SOLUTION_TEMPLATE.format(question=get_full_question(question), golden_solution=golden_solution, submitted_answer=submitted_answer) 
            response, is_json_success = self._get_json_response(CHECK_SOLUTION_PROMPT, solution_str)
            eval_dict["is_json_success"] = is_json_success
            eval_dict["check_sol_response"] = response

            # if failed,return
            if not is_json_success:
                return eval_dict
            
            print("Ground Truth Solution:")
            for k in question["solution"]:
                print(k)
            print(f"-----> Solution Evaluation Result:\n {str(response)}\n--------------------")

            if self.sol_check_reflection:
                reflection_str = solution_str + "\n" + json.dumps(response)
                reflect_reponse, is_reflect_success = self._get_json_response(SOLUTION_CHECKING_REFLECTION_PROMPT, reflection_str)
                print(f"-----> Solution Evaluation Reflection: \n{str(response)}\n--------------------")
                eval_dict["is_reflect_success"] = is_reflect_success
                eval_dict["check_sol_reflection"] = reflect_reponse
                if not is_reflect_success:
                    return eval_dict
                else:
                    response = reflect_reponse
            
            # calculate the reward based on the response
            discount_factor = 0.4
            # reverse the response
            current_reward = 1
            total_reward = 0
            step_eval = []
            for _, v in response.items():
                step_eval.append(v["decision"])
            # step_eval = list(response.values())
            step_eval.reverse()
            for b in step_eval:
                if b == "True":
                    total_reward += current_reward
                if total_reward == 1:
                    return 1
                current_reward *= discount_factor

            eval_dict["reward"] = total_reward
            # 1 2 3 4
            # False  False False True -> 1
            # False False True  False -> 0.3
            # True True True False -> 0.3     # 0.3 + 0.09 + 0.027 = 0.417
            # all false
            return eval_dict

    def check_single_response(self, question: dict, submitted_answer: str) -> dict:
        input_str = EVAL_ANSWER_TEMPLATE.format(question=get_full_question(question), golden_answer=question["answer"], submitted_answer=submitted_answer)
        response = self.client.create(messages=[
            msging(CHECK_ANSWER_PROMPT, role="system"), 
            msging(input_str, role="user")
        ])
        response = response.choices[0].message.content
        decision = re.search(r"Decision: (True|False)", response)
        decision = decision.group(1)
        print("Ground Truth Answer:", question["answer"])
        print(f"-----> Answer Evaluation Result: {response}")
        return_dict = {"check_ans_response": response, "reward": int(decision == "True")}

        if self.ans_check_reflection:
            messages=[
                msging(ANSWER_CHECKING_REFLECTION_PROMPT, role="system"), 
                msging(input_str+"\n"+response, role="user")
            ]
            reflect_response = self.client.create(messages=messages).choices[0].message.content
            return_dict["check_ans_reflection"] = reflect_response
            decision = re.search(r"Decision: (True|False)", reflect_response)
            decision = decision.group(1)
            return_dict['reward'] = int(decision == "True")
            print(f"-----> Answer Evaluation Reflection: {reflect_response}")
        return return_dict
        
        
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