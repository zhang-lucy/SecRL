from agents.baseline_agent import BaselineAgent
import json
from datetime import datetime
from typing import Union

from secgym.env.ThuGEnv import ThuGEnv
from secgym.myconfig import config_list_4o

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
    
    for i in range(thug_env.num_questions):
        observation, _ = thug_env.reset(i) # first observation is question dict
        agent.reset()

        # temp hack
        if "SecurityExposureManagement" in thug_env.curr_question['tables']:
            print(f"Skipping question {i+1}")
            continue
        
        # run one episode
        for s in range(thug_env.max_steps):
            print(f"Observation: {observation}")
            print("*"*50)
            action, submit = agent.act(observation)
            observation, reward, _, _ = thug_env.step(action=action, submit=submit)

            if submit:
                break
        
        accum_reward += reward
        accum_success += reward == 1

        result_dict ={
                "reward": reward,
                "success": reward == 1,
                "question_dict": thug_env.curr_question,
            }
        result_dict.update(agent.get_logging())
        accum_logs.append(result_dict)

        with open(save_agent_file, "w") as f:
            json.dump(accum_logs, f, indent=4)
        print(f"Question {i+1} | Reward: {reward} || Accumlated Success: {accum_success}/{i+1}={accum_success/(i+1):.3f} | Avg Reward so far: {accum_reward/(i+1):.3f}")  
        print("*"*50, "\n", "*"*50)

        if i == num_test:
            print(f"Tested {num_test} questions. Stopping...")
            break


if __name__ == "__main__":
    curr_time = datetime.now().strftime("%Y%m%d-%H%M%S")
    # save_agent_file = f"results/agent_log_{curr_time}.json"
    save_agent_file = f"results/agent_log.json"

    agent = BaselineAgent(
        config_list=config_list_4o,
        cache_seed=42
    )

    thug_env = ThuGEnv(
        attack="AAD_Comprise", 
        config_list=config_list_4o, 
        noise_level=0,
        save_file="results/aad_comprise.json"
    ) 
    run_experiment(
        agent=agent,
        thug_env=thug_env,
        save_agent_file=save_agent_file,
        num_test=5
    )
    