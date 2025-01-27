import json
from datetime import datetime
from typing import Union
import os
from secgym.env.ThuGEnv import ThuGEnv, ATTACKS
from secgym.myconfig import config_list_4o, config_list_4o_mini
from secgym.qagen.alert_graph import AlertGraph
import argparse
from secgym.agents import BaselineAgent, CheatingAgent, PromptSauceAgent, ReflexionAgent

#config_list_4_turbo, config_list_35

def run_experiment(
        agent,
        thug_env: ThuGEnv,
        save_agent_file: str,
        num_test: Union[int, None] = None,
        num_trials: int = 1
    ):
    if num_test is None:
        num_test = thug_env.num_questions

    accum_reward = 0
    accum_success = 0
    accum_logs = []
    tested_num = 0

    for i in range(thug_env.num_questions):
        #emptying the replay buffer for each question
        if agent.name == "ReflexionAgent":
            agent.replay_buffer = []
        tested_num += 1 # increment tested number of questions

        for trial in range(num_trials):
            if i == num_test:
                print(f"Tested {num_test} questions. Stopping...")
                break

            observation, _ = thug_env.reset(i) # first observation is question dict
            agent.reset()

            # run one episode
            for s in range(thug_env.max_steps):
                print(f"Observation: {observation}")
                print("*"*50)
                try:
                    action, submit = agent.act(observation)
                except Exception as e:
                    print(f"Error: {e}")
                    reward = 0
                    break
                observation, reward, _, _ = thug_env.step(action=action, submit=submit)

                if submit:
                    break
            
            # for Reflexion Agent
            # saving replay in agent memory
            replay = {
                "messages": agent.messages,
                "incident": agent.incident,
                "question": thug_env.curr_question,
                "reward": reward,
                "trial": trial,
            }
            if agent.name == "ReflexionAgent":
                agent.replay_buffer.append(replay)

            # printing logs
            print(f"Question {i+1} | Reward: {reward} || Accumlated Success: {accum_success}/{tested_num}={accum_success/(tested_num):.3f} | Avg Reward so far: {accum_reward/(tested_num):.3f}")  
            print("*"*50, "\n", "*"*50)

            #correct answer found -> stop trials
            if reward == 1:
                print(f"Skipping question {i+1} as it has been solved")
                break
        
        #saving logs
        result_dict = {
            "reward": reward,
            "nodes": f"{thug_env.curr_question['start_alert']}-{thug_env.curr_question['end_alert']}",
            "question_dict": thug_env.curr_question,
            "trial": trial,
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


def get_args():
    parser = argparse.ArgumentParser(description="Run Experienments")
    parser.add_argument("--model", "-m", type=str, default="gpt-4o", help="Model to use for experiment")
    parser.add_argument("--eval_model", "-e", type=str, default="gpt-4o", help="Model to use for evaluation")
    parser.add_argument("--cache_seed", type=int, default=111, help="Seed for the cache")
    parser.add_argument("--temperature", type=int, default=0, help="Temperature for the model")
    parser.add_argument("--max_steps", type=int, default=15, help="Maximum number of steps for the agent")
    parser.add_argument("--layer", type=str, default="alert", help="Layer to use for the agent")
    parser.add_argument("--eval_step", action="store_true", help="Evaluate each step")
    parser.add_argument("--agent", type=str, default="baseline", help="Agent to use for the experiment")
    parser.add_argument("--num_trials", type=int, default=1, help="Number of trials to run for each question if not solved")
    args = parser.parse_args()
    return args


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
    eval_step = args.eval_step
    num_trials = args.num_trials

    # need to be filled before running
    model_config_map = {
        #"gpt-3.5": config_list_35,
        "gpt-4o": config_list_4o,
        "gpt-4o-mini": config_list_4o_mini,
        #"gpt-4turbo": config_list_4_turbo,
    }
    agent_config_list = model_config_map[model]
    eval_config_list = model_config_map[eval_model]

    if args.agent == "baseline":
        test_agent = BaselineAgent(
            config_list=agent_config_list,
            cache_seed=cache_seed, 
            temperature=temperature,
            max_steps=max_steps,
        )
    # elif args.agent == "prompt_sauce":
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


    post_fix = f"_{model}_{cache_seed}_{layer}"
    os.makedirs("results", exist_ok=True)
    agent_name = test_agent.name

    for attack in ATTACKS:
        print(f"Running attack: {attack}")
        save_agent_file = f"results/{agent_name}_{attack}_agent_log{post_fix}.json"
        save_env_file = f"results/{agent_name}_{attack}_env_log{post_fix}.json"

        thug_env = ThuGEnv(
            attack=attack,
            eval_config_list=eval_config_list,
            noise_level=0,
            save_file=save_env_file,
            max_steps=max_steps,
            eval_step=eval_step,
        )
        thug_env.check_layer(layer) # check if revelant layer is in the database
        
        avg_success, tested_num, avg_reward = run_experiment(
            agent=test_agent,
            thug_env=thug_env,
            save_agent_file=save_agent_file,
            num_test=-1, # set to -1 to run all questions
            num_trials=num_trials,
        )
        test_agent.reset()

        with open('results.txt', 'a') as f:
            f.write(f"Model: {model}, Attack: {attack}, Agent: {agent_name}, Cache Seed: {cache_seed}, Temperature: {temperature}, Layer: {layer}, Max Steps: {max_steps}, Eval Model: {eval_model}\n")
            f.write(f"Success: {avg_success}/{tested_num}={avg_success/tested_num:.3f}, Avg Reward: {avg_reward/tested_num:.3f}\n")