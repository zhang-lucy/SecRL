import random
random.seed(0)

def analysis(data:dict, verbose:bool=False):
    """Analyze the data and print out the results

    Args:
        data (dict): The data to be analyzed, load an "agent log" json file
        
    """
    total_len = len(data)
    total_reward = 0
    total_round = 0
    non_zero_reward_count = 0
    non_success_count = 0

    path_count = {}
    reward_count = {}
    round_count = {}
    for k in data:
        p = len(k['question_dict']['shortest_alert_path'])
        if p not in path_count:
            path_count[p] = 0
            reward_count[p] = 0
            round_count[p] = 0

        if k['reward'] > 0 and k['reward'] < 1:
            non_success_count += 1
        if k['reward'] > 0:
            non_zero_reward_count += 1
        
        # total
        total_reward += k['reward']
        total_round += (len(k["messages"]) - 1) // 2

        path_count[p] += 1
        reward_count[p] += k['reward']
        round_count[p] += (len(k["messages"]) - 1) // 2

    if verbose:
        print(f"Average reward: {total_reward}/{total_len} = {round(total_reward/total_len,6)}")
        print(f"Average round: {total_round}/{total_len} = {round(total_round/total_len,6)}")
        # print(f"Non success / non-zero reward count: {non_success_count}/{non_zero_reward_count}")

        # sorted_keys = sorted(path_count.keys())
        # for k in sorted_keys:
        #     print(f"Difficulty {k}: {round(reward_count[k], 2)}/{path_count[k]} = {round(reward_count[k]/path_count[k],6)} | Avg round: {round(round_count[k]/path_count[k], 2)}")


    return {
        "total_len": total_len,
        "total_reward": total_reward,
        "total_round": total_round,
        "non_zero_reward_count": non_zero_reward_count,
        "non_success_count": non_success_count,
        "path_count": path_count,
        "reward_count": reward_count,
        "round_count": round_count
    }

import json

def analysis_one_run(log_path, file_template, print_total=False, sample_size=-1):

    incidents = [55, 5, 34, 38, 134, 166, 39, 322]

    total_len = 0
    total_reward = 0
    total_round = 0
    path_count = {}
    reward_count = {}

    all_data = []
    for i in incidents:
        if not print_total:
            print("*"*20)
            print(f"Analysis for incident {i}")

        a = open(f"{log_path}/{file_template.format(i)}", "r")
        b = json.load(a)
        all_data.extend(b)
    print(len(all_data))
        
    random.shuffle(all_data)
    if sample_size > 0:
        # sample_size is the size for each difficulty, For difficulty 1 3 5 7 9, we will sample sample_size number of incidents
        # go through the data and sample sample_size number for each difficulty
        # go through each problem, if the difficulty reaches sample_size, won't append it
        sampled_data = []
        sampled_count = {}
        for k in all_data:
            p = len(k['question_dict']['shortest_alert_path'])
            if p not in sampled_count:
                sampled_count[p] = 0
            if sampled_count[p] < sample_size:
                sampled_data.append(k)
                sampled_count[p] += 1
        all_data = sampled_data
        
    result_dict = analysis(all_data, not print_total)

    total_len += result_dict['total_len']
    total_reward += result_dict['total_reward']
    total_round += result_dict['total_round']
    for k in result_dict['path_count']:
        if k not in path_count:
            path_count[k] = 0
            reward_count[k] = 0

        path_count[k] += result_dict['path_count'][k]
        reward_count[k] += result_dict['reward_count'][k]
    if not print_total:
        print("*"*20)
        
    if print_total:
        print("*"*40)
        print("*"*40)
        print("Total analysis")
        print(f"Total length: {total_len}")
        print(f"Total reward: {total_reward}")
        print(f"Total round: {total_round}")
        print(f"Average reward: {total_reward}/{total_len} = {round(total_reward/total_len,6)}")
        print(f"Average round: {total_round}/{total_len} = {round(total_round/total_len,6)}")

        sorted_keys = sorted(path_count.keys())
        for k in sorted_keys:
            print(f"Difficulty {k}: {round(reward_count[k], 2)}/{path_count[k]} = {round(reward_count[k]/path_count[k],6)}")


def get_correct_problem_ids(log_path, file_template, incident_id):
    a = open(f"{log_path}/{file_template.format(incident_id)}", "r")
    b = json.load(a)
    correct_ids = []
    for k in b:
        if k['reward'] == 1:
            correct_ids.append(k['question_id'])
    return correct_ids
