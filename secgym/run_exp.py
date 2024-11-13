from agents.baseline_agent import BaselineAgent
import json
from datetime import datetime
from typing import Union
import os
from secgym.env.ThuGEnv import ThuGEnv, ATTACKS
from secgym.myconfig import config_list_4o 
#config_list_4_turbo, config_list_35

def run_experiment(
        agent,
        thug_env: ThuGEnv,
        save_agent_file: str,
        num_test: Union[int, None] = None
    ):
    if num_test is None:
        num_test = thug_env.num_questions

    accum_reward = 0
    accum_success = 0
    accum_logs = []
    tested_num = 0

    # open a json:
    # with open("results/agent_log_hint_4.json", "r") as f:
    #     trial_1 = json.load(f)

    for i in range(thug_env.num_questions):
        if i == num_test:
            print(f"Tested {num_test} questions. Stopping...")
            break
        observation, _ = thug_env.reset(i) # first observation is question dict
        agent.reset()

        # if trial_1[i]['reward'] == 1:
        #     print(f"Skipping question {i+1} as it has been solved")
        #     continue
        # tmp = (thug_env.curr_question['start_node'], thug_env.curr_question['end_node'])
        # if tmp not in [(12, 6), (6, 12), (8, 14), (14, 8), (14, 10), (14, 4), (4, 10), (4, 3)]:
        #     continue
        # temp hack
        # if "SecurityExposureManagement" in thug_env.curr_question['tables']:
        #     print(f"Skipping question {i+1}")
        #     continue

        tested_num += 1 
        
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
        
        accum_reward += reward
        accum_success += reward == 1

        result_dict ={
                "reward": reward,
                "nodes": f"{thug_env.curr_question['start_alert']}-{thug_env.curr_question['end_alert']}",
                "question_dict": thug_env.curr_question,
            }
        result_dict.update(agent.get_logging())
        accum_logs.append(result_dict)

        with open(save_agent_file, "w") as f:
            json.dump(accum_logs, f, indent=4)
        print(f"Question {i+1} | Reward: {reward} || Accumlated Success: {accum_success}/{tested_num}={accum_success/(tested_num):.3f} | Avg Reward so far: {accum_reward/(tested_num):.3f}")  
        print("*"*50, "\n", "*"*50)
    
    return accum_success, tested_num, accum_reward

if __name__ == "__main__":
    curr_time = datetime.now().strftime("%Y%m%d-%H%M%S")
    # save_agent_file = f"results/agent_log_{curr_time}.json"
    # cache_seed = 44
    # agent_config_list = config_list_4o

    cache_seed = 46
    temperature = 0
    add_hint = False
    model = "gpt-4o"
    submit_summary = False
    max_steps = 15

    model_config_map = {
        #"gpt-3.5": config_list_35,
        "gpt-4o": config_list_4o,
        #"gpt-4turbo": config_list_4_turbo,
    }
    agent_config_list = model_config_map[model]

    post_fix = f"_{model}_{cache_seed}"
    if add_hint:
        post_fix += "_hint"
    if submit_summary:
        post_fix += "_sum"

    os.makedirs("results", exist_ok=True)

    agent = BaselineAgent(
        config_list=agent_config_list,
        cache_seed=cache_seed, 
        submit_summary=submit_summary,
        temperature=temperature,
    )

    for attack in ATTACKS:
        print(f"Running attack: {attack}")
        save_agent_file = f"results/{attack}_agent_log{post_fix}.json"
        save_env_file = f"results/{attack}_env_log{post_fix}.json"

        thug_env = ThuGEnv(
            attack=attack,
            config_list=config_list_4o, 
            noise_level=0,
            save_file=save_env_file,
            add_hint=add_hint,
            max_steps=max_steps,
            eval_step=True,
        ) 
        avg_success, tested_num, avg_reward = run_experiment(
            agent=agent,
            thug_env=thug_env,
            save_agent_file=save_agent_file,
            num_test=-1 # set to -1 to run all questions
        )
        agent.reset()

        with open('results.txt', 'a') as f:
            f.write(f"Model: {model}, Cache Seed: {cache_seed}, Hint: {add_hint}, Submit Summary: {submit_summary}, Temperature: {temperature}\n")
            f.write(f"Success: {avg_success}/{tested_num}={avg_success/tested_num:.3f}, Avg Reward: {avg_reward/tested_num:.3f}\n")