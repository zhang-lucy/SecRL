
import json
import os
from pathlib import Path
from typing import Dict, List, Literal, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats

import autogen
from agent_eval.agent_eval import generate_criteria, quantify_criteria
from agent_eval.criterion import Criterion
from agent_eval.task import Task
from agent_eval.quantifier_agent import QuantifierAgent

from secgym.myconfig import config_list_4o


def format_question_str(question:dict):
    base = f"Question: {question['question_dict']['question']}\nCorrect Answer: {question['question_dict']['answer']}\n"
    if "solution" in question['question_dict']:
        base += f"Correct Solution: {question['question_dict']['solution']}\n"
    base += f"Agent Investigation steps: {question['messages']}"
    return base

def remove_ground_truth(test_case):
    test_details = json.loads(test_case)
    # need to remove the ground truth from the test details
    correctness = test_details.pop("is_correct", None)
    test_details.pop("correct_ans", None)
    test_details.pop("check_result", None)
    return str(test_details), correctness

def calculate_results(criteria, quantifier_output):
    single_criteria_weight = 1 / len(criteria)

    final_score = 0

    try:
        estimated_performance = json.loads(quantifier_output["estimated_performance"])
    except Exception as e:
        print(e)
        estimated_performance = {"str_result": quantifier_output["estimated_performance"]}

    for criterion in criteria:
        if criterion.name in estimated_performance:
            # print(f"Criterion: {criterion.name}, Value: {estimated_performance[criterion.name]}, Weight: {(1-0.2*criterion.accepted_values.index(estimated_performance[criterion.name]))}")
            final_score += single_criteria_weight * (1-0.2*criterion.accepted_values.index(estimated_performance[criterion.name]))
        else:
            raise ValueError(f"Criterion {criterion.name} not found in estimated performance.")
    
    estimated_performance["final_score"] = final_score
    return estimated_performance


config_list = config_list_4o


# get the criteria
criteria_file = f"./selected_criteria.json"
criteria = open(criteria_file, "r").read()
criteria = Criterion.parse_json_str(criteria)

# get correct and wrong questions
with open('../../../../results/agent_log_gpt-4o_46_sum.json') as f:
    data = json.load(f)
correct_q, wrong_q = [], []
for i in range(len(data)):
    if data[i]['reward'] == 1:
        correct_q.append(data[i])
    elif data[i]['reward'] == 0:
        wrong_q.append(data[i])

# get the task
task = Task(
    **{
        "name": "Investigation of an security question.",
        "description": "A security question is asked, and we have the investigation of this question.",
        "successful_response": format_question_str(correct_q[0]),
        "failed_response": format_question_str(wrong_q[0]),
        # "successful_response": "No successful response",
        # "failed_response": "No failed response",
    }
)

# cd .\agent_eval\autogen\notebook\attacks\

scores = []
for i, d in enumerate(data):
    test_example = d
    # print(len(format_question_str(test_example)))

    quantifier_output = quantify_criteria(
        llm_config={"config_list": config_list, "response_format": {'type': 'json_object'}, "cache_seed": 42},
        criteria=criteria,
        task=task,
        test_case=format_question_str(test_example),
        silent=True,
        # ground_truth=ground_truth,
    )

    results = calculate_results(criteria, quantifier_output)

    # print(f"Question {i+1}:Results:\n{results}")
    print(f"score: {results['final_score']}, Is_correct: {d['reward']}, Message Len: {len(d['messages'])}\n\n\n")

    scores.append(results['final_score'])

# get mean, and std

mean = np.mean(scores)
std = np.std(scores)
print(f"Mean: {mean}, Std: {std}")


# print("actual correctness:", quantifier_output["actual_success"])
# print("predicted correctness:\n", quantifier_output["estimated_performance"])



        

    
