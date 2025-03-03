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

#config_list_4_turbo, config_list_35

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
                "reward": reward,
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

#TODO: fix eval step default value
def get_args():
    parser = argparse.ArgumentParser(description="Run Experienments")
    parser.add_argument("--model", "-m", type=str, default="gpt-4o", help="Model to use for experiment")
    parser.add_argument("--eval_model", "-e", type=str, default="gpt-4o", help="Model to use for evaluation")
    parser.add_argument("--cache_seed", type=int, default=103, help="Seed for the cache")
    parser.add_argument("--temperature", type=int, default=0, help="Temperature for the model")
    parser.add_argument("--max_steps", type=int, default=25, help="Maximum number of steps for the agent")
    parser.add_argument("--layer", type=str, default="alert", help="Layer to use for the agent")
    #parser.add_argument("--step_checking", action="store_true", help="Evaluate each step")
    parser.add_argument("--agent", type=str, default="baseline", help="Agent to use for the experiment")
    parser.add_argument("--num_trials", type=int, default=1, help="Number of trials to run for each question if not solved")
    parser.add_argument("--split", type=str, default="test", help="Split to use for the experiment")
    args = parser.parse_args()
    return args

import autogen
def filter_config_list(config_list, model_name):
    config_list = autogen.filter_config(config_list, {'tags': [model_name]})
    if len(config_list) == 0:
        raise ValueError(f"model {model_name} not found in the config list, please put 'tags': ['{model_name}'] in the config list to inicate this model")
    return config_list

if __name__ == "__main__":
    # curr_time = datetime.now().strftime("%Y%m%d-%H%M%S")
    args = get_args()

    model = args.model
    eval_model = args.eval_model
    cache_seed = args.cache_seed
    temperature = args.temperature
    max_steps = args.max_steps
    assert args.layer in ["log", "alert"], "Layer must be either 'log' or 'alert'"
    layer = args.layer
    num_trials = args.num_trials

    agent_config_list = filter_config_list(CONFIG_LIST, model)
    eval_config_list = filter_config_list(CONFIG_LIST, eval_model)

    evaluator = Evaluator(
        config_list=eval_config_list, 
        ans_check_reflection=True, 
        sol_check_reflection=True,
        step_checking=True,
        strict_check=False,
    )

    if args.agent == "baseline":
        test_agent = BaselineAgent(
            config_list=agent_config_list,
            cache_seed=cache_seed, 
            temperature=temperature,
            max_steps=max_steps,
        )
    elif args.agent == "prompt_sauce":
        test_agent = PromptSauceAgent(
            config_list=agent_config_list,
            cache_seed=cache_seed, 
            temperature=temperature,
            max_steps=max_steps,
        )
    elif args.agent == "reflexion":
        test_agent = ReflexionAgent(
            config_list=agent_config_list,
            cache_seed=cache_seed, 
            temperature=temperature,
            max_steps=max_steps,
        )
    elif args.agent == "multi_model_baseline":
        agent_config_list_master = filter_config_list(CONFIG_LIST, "o3-mini")
        test_agent = MultiModelBaselineAgent(
            config_list_master=agent_config_list_master,
            config_list_slave=agent_config_list,
            cache_seed=cache_seed, 
            temperature=temperature,
            max_steps=max_steps,
        )
    elif args.agent == "cheating":
        pass
        # # For cheating agent
        # graph_path = f"qagen/graph_files/{attack}.graphml"
        # alert_graph = AlertGraph()
        # alert_graph.load_graph_from_graphml(graph_path)
        # incident = alert_graph.incident
        # agent.incident = incident
        # # print(incident)
        # # exit()
    else:
        raise ValueError(f"Invalid agent name: {args.agent}, please modify run_exp.py to include the agent")

    base_dir = "final_results"
    os.makedirs(base_dir, exist_ok=True)
    agent_name = test_agent.name

    sub_dir = f"{agent_name}_{model}_c{cache_seed}_{layer}_level_t{temperature}_s{max_steps}_trial{num_trials}"
    if args.split != "test":
        sub_dir += f"_{args.split}"
    os.makedirs(f"{base_dir}/{sub_dir}", exist_ok=True)

    for attack in ATTACKS:
        print(f"Running attack: {attack}")
        save_agent_file = f"{base_dir}/{sub_dir}/agent_{attack}.json" 
        save_env_file = f"{base_dir}/{sub_dir}/env_{attack}.json"

        thug_env = ThuGEnv(
            attack=attack,
            evaluator=evaluator,
            save_file=save_env_file,
            max_steps=max_steps,
            split=args.split,
        )
        thug_env.check_layer(layer) # check if revelant tables is in the database for the layer
        
        avg_success, tested_num, avg_reward = run_experiment(
            agent=test_agent,
            thug_env=thug_env,
            save_agent_file=save_agent_file,
            num_test=-1, # set to -1 to run all questions
            num_trials=num_trials,
        )
        test_agent.reset()

        with open(f'{base_dir}/{sub_dir}/results.txt', 'a') as f:
            f.write(f"Model: {model}, Attack: {attack}, Agent: {agent_name}, Cache Seed: {cache_seed}, Temperature: {temperature}, Layer: {layer}, Max Steps: {max_steps}, Eval Model: {eval_model}, Num Trials: {num_trials}\n")
            f.write(f"Success: {avg_success}/{tested_num}={avg_success/tested_num:.3f}, Avg Reward: {avg_reward/tested_num:.3f}\n")