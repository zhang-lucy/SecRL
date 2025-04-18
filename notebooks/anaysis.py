import random
random.seed(0)
import json

def analysis(data:dict, verbose:bool=False, round_cut=-1):
    """Analyze the data and print out the results

    Args:
        data (dict): The data to be analyzed, load an "agent log" json file
        
    """
    if round_cut != -1 and "trials" in data[0]:
        # print("Warning: use round_cut with trial data")
        pass
    total_len = len(data)
    total_reward = 0
    total_round = 0
    
    success_count = 0 # reward == 1
    non_zero_reward_count = 0 # reward > 0
    submit_count = 0

    path_count = {}
    reward_count = {} # reward for each difficulty
    round_count = {}
    eval_error_count = 0

    # cost
    total_cost = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0

    # query efficiency
    empty_result_count = 0
    error_query_count = 0
    query_count = 0

    success_non_empty_query_count = 0
    potential_good_example_count = 0

    fail_to_run_count = 0
    max_round = 0
    min_round = 1000

    for k in data:
        if "trials" not in k and k.get("usage_summary") is None:
            print(f"No usage summary, skipping {k['nodes']}")
            fail_to_run_count += 1
            continue

        p = len(k['question_dict']['shortest_alert_path'])
        if p not in path_count:
            path_count[p] = 0
            reward_count[p] = 0
            round_count[p] = 0

        # situation 1: "trials" not in k
        if "trials" not in k:
            tmp_round = (len(k["messages"]) - 1) // 2
            if round_cut != -1 and tmp_round > round_cut:
                # print(f"Cutting off at round {round_cut}")
                k['reward'] = 0
                tmp_round = round_cut
            total_round += tmp_round
            total_reward += k['reward']
            if k['reward'] > 0:
                non_zero_reward_count += 1
            if k['reward'] == 1:
                success_count += 1
            path_count[p] += 1
            reward_count[p] += k['reward']
            total_cost, total_prompt_tokens, total_completion_tokens = add_to_usage(k['usage_summary'], total_cost, total_prompt_tokens, total_completion_tokens)
        else:
            raise NotImplementedError("Not implemented for question dict with trials field, use another function")
            
    if verbose:
        print(f"Average reward: {total_reward}/{total_len} = {round(total_reward/total_len,6)}")
        print(f"Average round: {total_round}/{total_len} = {round(total_round/total_len,6)}")


    return {
        "total_len": total_len,

        # Performance Analysis
        "total_reward": total_reward,
        "success_count": success_count, # reward==1
        "non_zero_reward_count": non_zero_reward_count, # for evaluator usefullness
        "submit_count": submit_count,

        # Efficiency / Computational Analysis
        "total_cost": total_cost,
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,

        # Query Efficiency
        "empty_result_count": empty_result_count,
        "error_query_count": error_query_count,
        "query_count": query_count,

        # Evaluation Analysis
        "eval_error_count": eval_error_count,
        "fail_to_run_count": fail_to_run_count
    }
def analysis_v2(data:dict, verbose:bool=False, round_cut=-1):
    """Analyze the data and print out the results

    Args:
        data (dict): The data to be analyzed, load an "agent log" json file
        verbose (bool, optional): Whether to print verbose output. Defaults to False.
        round_cut (int, optional): Maximum round to consider. Defaults to -1 (no cut).
    """
    total_len = len(data)
    total_reward = 0
    total_round = 0
    
    success_count = 0 # reward == 1
    non_zero_reward_count = 0 # reward > 0
    not_submit_count = 0

    path_count = {}
    reward_count = {} # reward for each difficulty
    round_count = {}
    eval_error_count = 0

    # cost
    total_cost = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0

    # query efficiency
    empty_result_count = 0
    error_query_count = 0
    query_count = 0

    success_non_empty_query_count = 0
    potential_good_example_count = 0

    fail_to_run_count = 0
    max_round = 0
    min_round = 1000

    for k in data:
        p = len(k['question_dict']['shortest_alert_path'])
        if p not in path_count:
            path_count[p] = 0
            reward_count[p] = 0
            round_count[p] = 0

        assert "trials" in k, "Expecting trials in question dict"
        assert len(k['trials']) == 1, f"Expecting only one trial, got {len(k['trials'])}"
        
        last_trial = list(k["trials"].values())[-1]
        
        # Apply round cut if specified
        tmp_round = (len(last_trial.get("messages", [])) - 1) // 2
        if round_cut != -1 and tmp_round > round_cut:
            reward = 0  # Set reward to 0 if exceeding round cut
            tmp_round = round_cut
        else:
            reward = k['reward']
        
        total_round += tmp_round

        # 1. count reward
        total_reward += reward
        if reward > 0:
            non_zero_reward_count += 1
        if reward == 1:
            success_count += 1
        path_count[p] += 1
        reward_count[p] += reward
        
        # 2. count usage
        try:
            model = list(last_trial['usage_summary'].keys())[-1]
            total_prompt_tokens += last_trial['usage_summary'][model]['prompt_tokens']
            total_completion_tokens += last_trial['usage_summary'][model]['completion_tokens']
        except Exception as e:
            print(f"Error calculating usage: usage summary {last_trial['usage_summary']}")
        
        # 4. check if submitted, if evaluated correctly
        if not last_trial['info'].get("submit"):
            not_submit_count += 1
        else:
            if not (last_trial['info'].get("is_json_success", True) and last_trial['info'].get("is_reflect_success", True)):
                print(f"Eval error for {k['nodes']}", last_trial['info'])
                eval_error_count += 1

    if verbose:
        print(f"Average reward: {total_reward}/{total_len} = {round(total_reward/total_len,6)}")
        print(f"Average round: {total_round}/{total_len} = {round(total_round/total_len,6)}")

    return {
        "total_len": total_len,

        # Performance Analysis
        "total_reward": total_reward,
        "success_count": success_count, # reward==1
        "non_zero_reward_count": non_zero_reward_count, # for evaluator usefullness
        "not_submit_count": not_submit_count, # not counting for now
        
        # Round information
        "total_round": total_round,

        # Efficiency / Computational Analysis
        "total_cost": total_cost,
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,

        # Query Efficiency
        "empty_result_count": empty_result_count,
        "error_query_count": error_query_count,
        "query_count": query_count,

        # Evaluation Analysis
        "eval_error_count": eval_error_count,
        "fail_to_run_count": fail_to_run_count
    }

def add_to_usage(usage_summary:dict, total_cost=0, total_prompt_tokens=0, total_completion_tokens=0):
    model = list(usage_summary.keys())[-1]
    total_cost += usage_summary[model]['cost']
    total_prompt_tokens += usage_summary[model]['prompt_tokens']
    total_completion_tokens += usage_summary[model]['completion_tokens']
    return total_cost, total_prompt_tokens, total_completion_tokens    

def print_analysis(result_dict:dict, head:str=None):
    print("*"*40)
    if head:
        print(f"{head} analysis")
    problem_count = result_dict['total_len']

    print(f"Average reward: {result_dict['total_reward']}/{problem_count} = {round(result_dict['total_reward']/problem_count,4)}")
    print(f"Success rate: {result_dict['success_count']}/{problem_count} = {round(result_dict['success_count']/problem_count * 100,2)}%")
    
    # Computational Analysis
    print(f"** Computational Analysis:")
    print(f"Average round: {result_dict['total_round']}/{problem_count} = {round(result_dict['total_round']/problem_count,4)}")
    print(f"Average cost: {result_dict['total_cost']}/{problem_count} = {round(result_dict['total_cost']/problem_count,4)}")
    print(f"Average prompt tokens: {result_dict['total_prompt_tokens']}/{problem_count} = {round(result_dict['total_prompt_tokens']/problem_count,4)}")
    print(f"Average completion tokens: {result_dict['total_completion_tokens']}/{problem_count} = {round(result_dict['total_completion_tokens']/problem_count,4)}")

    print("** Query Efficiency: ")
    success_query_count = result_dict['query_count'] - result_dict['error_query_count']
    print(f'Success Query rate: {success_query_count}/{result_dict["query_count"]} = {round(success_query_count/result_dict["query_count"] * 100,2)}%')
    print(f'Success Non-Empty Query rate: {success_query_count-result_dict["empty_result_count"]}/{result_dict["query_count"]} = {round((success_query_count-result_dict["empty_result_count"])/result_dict["query_count"] * 100,2)}%')
    
    print(f"Potential Good Example Count: {result_dict['potential_good_example_count']} / {problem_count}")
    print(f"Fail to run count: {result_dict['fail_to_run_count']}")

def get_correct_problem_ids(log_path, file_template, incident_id):
    a = open(f"{log_path}/{file_template.format(incident_id)}", "r")
    b = json.load(a)
    correct_ids = []
    for k in b:
        if k['reward'] == 1:
            correct_ids.append(k['question_id'])
    return correct_ids



def get_over_leaf_format(log_path, file_folder, version="v1", round_cut=-1):
    file_template = f"{log_path}/{file_folder}" + "/agent_incident_{0}.json"

    total_count = 0
    total_reward = 0
    total_success_count = 0
    total_cost = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0

    accs_str = ""

    incidents = [5, 34, 38, 39, 55, 134, 166, 322]
    for i in incidents:
        # print(f"Analysis for incident {i}")
        with open(file_template.format(i), "r") as f:
            data = json.load(f)
        if version == "v2":
            result = analysis_v2(data, False)
        else:
            result = analysis(data, False, round_cut)
        # print(result)
        accs_str += "& " + str(round(result['total_reward']/result['total_len'], 3)) + " "

        total_count += result['total_len']
        total_reward += result['total_reward']
        total_success_count += result['success_count']
        total_cost += result['total_cost']
        total_prompt_tokens += result['total_prompt_tokens']
        total_completion_tokens += result['total_completion_tokens']
    
    accs_str += "& " + str(round(total_reward/total_count, 3)) + " "
    print(total_count)
    # accs_str += "& " + str(round(total_cost/total_count, 3)) + " "
    print(accs_str)
    return round(total_reward/total_count, 3)