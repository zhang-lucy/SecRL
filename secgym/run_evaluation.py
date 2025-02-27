import json
from datetime import datetime
from typing import Union
import os
from secgym.env.ThuGEnv import ThuGEnv, ATTACKS
from secgym.env.evaluator import Evaluator
from secgym.myconfig import config_list_4o, config_list_4o_mini, CONFIG_LIST
from secgym.qagen.alert_graph import AlertGraph
import argparse
from secgym.agents import BaselineAgent, CheatingAgent, PromptSauceAgent, ReflexionAgent, MultiModelBaselineAgent
from secgym.utils import get_full_question
#config_list_4_turbo, config_list_35
import autogen
from secgym.agents.agent_utils import sql_parser
import sys



def run_experiment(
        agent,
        thug_env: ThuGEnv,
        save_agent_file: str,
        num_test: Union[int, None] = None,
        num_trials: int = 1,
        overwrite: bool = False,
    ):
    if num_test is None:
        num_test = thug_env.num_questions

    accum_reward = 0
    accum_success = 0
    accum_logs = []
    tested_num = 0
    tested_question_keys = set()

    # load logs if not overwrite
    if not overwrite and os.path.exists(save_agent_file):
        with open(save_agent_file, "r") as f:
            accum_logs = json.load(f)
            accum_reward = sum([log["reward"] for log in accum_logs])
            accum_success = sum([log["reward"]==1 for log in accum_logs])
            tested_num = len(accum_logs)
            tested_question_keys = set([log["nodes"] for log in accum_logs])
            print(f"Loaded logs from {save_agent_file}")
        
    for i in range(thug_env.num_questions):
        #emptying the replay buffer for each question
        if agent.name == "ReflexionAgent":
            agent.replay_buffer = []
        tested_num += 1 # increment tested number of questions

        trials = {}
        for trial in range(num_trials):
            if i == num_test:
                print(f"Tested {num_test} questions. Stopping...")
                break
            
            # reset environment and agent
            observation, _ = thug_env.reset(i) # first observation is question dict
            agent.reset()

            # check if question has been tested before
            current_question_key = f"{thug_env.curr_question['start_alert']}-{thug_env.curr_question['end_alert']}"
            if current_question_key in tested_question_keys:
                print(f"Skipping question with key {current_question_key}")

            # run one episode
            for s in range(thug_env.max_steps):
                print(f"Observation: {observation}")
                print("*"*50)
                try:
                    action, submit = agent.act(observation)
                except Exception as e:
                    print(f"Error: {e}")
                    info = {}
                    reward = 0
                    break
                observation, reward, _, info = thug_env.step(action=action, submit=submit)

                if submit:
                    break
            
            # for Reflexion Agent
            if agent.name == "ReflexionAgent":
                # saving replay in agent memory
                replay = {
                    "messages": agent.messages,
                    "incident": agent.incident,
                    "question": thug_env.curr_question,
                    "reward": reward,
                    "trial": trial,
                }
                agent.replay_buffer.append(replay)
            
            # printing logs
            print(f"Question {i+1} | Reward: {reward} || Accumlated Success: {accum_success}/{tested_num}={accum_success/(tested_num):.3f} | Avg Reward so far: {accum_reward/(tested_num):.3f}")  
            print("*"*50, "\n", "*"*50)

            trials[trial] = {
                reward: reward,
                "info": info,
            }
            trials[trial].update(agent.get_logging())

            # correct answer found -> stop trials
            if reward == 1:
                print(f"Skipping question {i+1} as it has been solved")
                break

        
        #saving logs
        result_dict = {
            "nodes": current_question_key,
            "reward": reward,
            "question_dict": thug_env.curr_question,
            "trials": trials,
        }
        result_dict.update(agent.get_logging())
        accum_logs.append(result_dict)
        accum_reward += reward
        accum_success += reward == 1

        with open(save_agent_file, "w") as f:
            json.dump(accum_logs, f, indent=4)
        print(f"Question {i+1} | Reward: {reward} || Accumlated Success: {accum_success}/{tested_num}={accum_success/(tested_num):.3f} | Avg Reward so far: {accum_reward/(tested_num):.3f}")  
        print("*"*50, "\n", "*"*50)
    
    return accum_success, tested_num, accum_reward


def run_evaluation(
    evaluator: Evaluator,
    save_agent_file: str,
    save_env_file: str,
    # base_file: str,
    is_update_file: bool = False,
):
    """
    Run evaluation on the agent logs"
    """
    with open(save_agent_file, "r") as f:
        agent_log = json.load(f)
    
    with open(save_env_file, "r") as f:
        env_log = json.load(f)

    # print(f"len agent log: {len(agent_log)} | len env log: {len(env_log)}")
    reevaluated_count = 0
    changed_reward = 0

    for i, agent_log_entry in enumerate(agent_log):
        if "info" in agent_log_entry:
            info = agent_log_entry["info"]
            last_message = agent_log_entry["messages"][-1]['content']
        else:
            info = agent_log_entry['trials']["0"]["info"] # assume only one trial
            last_message = agent_log_entry['trials']["0"]["messages"][-1]['content']

        if "submit" not in info:
            print(agent_log_entry['nodes'], save_agent_file, info)
            continue
        
        if i < len(env_log):
            assert agent_log_entry['question_dict']['start_alert'] == env_log[i]['question']['start_alert']
            assert agent_log_entry['question_dict']['end_alert'] == env_log[i]['question']['end_alert']
        
        if not info['submit']:
            continue # skip if not submitted
        
        # get env log entry
        # if submit, last action is the submitted answer
        if i < len(env_log):
            submitted_answer = env_log[i]['trajectory'][-1]['action']
        else:
            submitted_answer, _, is_submit = sql_parser(last_message)

        old_reward = agent_log_entry["reward"]

        # re-evaluate
        eval_dict = evaluator.checking(question=agent_log_entry["question_dict"], submitted_answer=submitted_answer)
        reevaluated_count += 1

        # ------------------------------------
        info.update(eval_dict) # update info with eval results

        # update agent log entry
        agent_log_entry['reward'] = eval_dict["reward"]
        if "info" in agent_log_entry:
            agent_log_entry["info"] = info
        else:
            agent_log_entry["0"]["info"] = info
        
        # update env log entry
        if i < len(env_log):
            env_log[i]['reward'] = eval_dict["reward"]
            env_log[i]['trajectory'][-1]['reward'] = eval_dict["reward"]
            env_log[i]['trajectory'][-1]['info'] = info
        
        if eval_dict['reward'] != old_reward:
            changed_reward += 1
            with open('test.txt', 'a') as sys.stdout:
                print(f"question {agent_log_entry['nodes']} | reward: {old_reward} -> {eval_dict['reward']}")
                print("Submitted Answer", submitted_answer)
                print("Correct Answer", agent_log_entry["question_dict"]['answer'])
                print("Evaluation", eval_dict['check_ans_response'])
                print("Reflection on Explanation", eval_dict['check_ans_reflection'])

    print(f"Re-evaluated {reevaluated_count} questions | Changed reward: {changed_reward}")

    if is_update_file:
        with open(save_agent_file, "w") as f:
            json.dump(agent_log, f, indent=4)
        with open(save_env_file, "w") as f:
            json.dump(env_log, f, indent=4)


# check if submit
# no submit -> 0

# data
# data['reward']
# if data['info'] doesn't exist -> data['info']['1'] or data['info']['0'] find info 
# 

def filter_config_list(config_list, model_name):
    config_list = autogen.filter_config(config_list, {'tags': [model_name]})
    if len(config_list) == 0:
        raise ValueError(f"model {model_name} not found in the config list, please put 'tags': ['{model_name}'] in the config list to inicate this model")
    return config_list

if __name__ == "__main__":
    eval_model = "gpt-4o"
    cache_seed = 102
    temperature = 0
    eval_config_list = filter_config_list(CONFIG_LIST, eval_model)
    evaluator = Evaluator(
        config_list=eval_config_list, 
        ans_check_reflection=True, 
        sol_check_reflection=True,
        step_checking=True,
        strict_check=False,
    )

    base_files = [
        "BaselineAgent_4o-mini_c71_alert_level_t0_s25_trial1",
        "BaselineAgent_gpt-4o_c70_alert_level_t0_s25_trial1",
        "BaselineAgent_gpt-4o_c102_alert_level_t0_s25_trial1_train",
        "BaselineAgent_gpt-4o-ft-cv1_c102_alert_level_t0_s25_trial1",
        "BaselineAgent_o1-mini_c92_alert_level_t0_s25_trial1",
        "BaselineAgent_o3-mini_c99_alert_level_t0_s25_trial1",

        # new ones: info only in trias['i']['info']
        "MultiModelBaselineAgent_master_o1_mini_slave_gpt-4o_c96_alert_level_t0_s25_trial1",
        "MultiModelBaselineAgent_master_o1_slave_gpt-4o_c98_alert_level_t0_s25_trial1",
        "MultiModelBaselineAgent_master_o3_mini_slave_gpt-4o_c100_alert_level_t0_s25_trial1",
    ]

    consider_rerun = [
         "PromptSauceAgent_4o-mini_c73_alert_level_t0_s25_trial1",# rerun 3 trials
         "PromptSauceAgent_gpt-4o_c72_alert_level_t0_s25_trial1", # rerun 3 trials
         "PromptSauceAgent_4o-mini_c79_alert_level_t0_s15_trial2", # no need to run
         "PromptSauceAgent_gpt-4o_c83_alert_level_t0_s15_trial2", # no need to run
    ] # On Hold
    reflections = [
        "ReflexionAgent_gpt-4o_c101_alert_level_t0_s15_trial3_train",
        "ReflexionAgent_gpt-4o_c82_alert_level_t0_s15_trial3",
        "ReflexionAgent_4o-mini_c80_alert_level_t0_s15_trial3",
    ] # On Hold

    for base_file in base_files:
        print(f"Running evaluation for {base_file}")
        for attack in ATTACKS:
            print(f"Running evaluation for {attack}")
            # avg_success, tested_num, avg_reward = 
            run_evaluation(
                evaluator=evaluator,
                save_agent_file=f"./final_results/{base_file}/agent_{attack}.json",
                save_env_file=f"./final_results/{base_file}/env_{attack}.json",
                #base_file=base_file,
                is_update_file=True,
            )