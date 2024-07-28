from agents.baseline_agent import BaselineAgent
import json
from datetime import datetime

from secgym.env.ThuGEnv import ThuGEnv
from secgym.myconfig import config_list_4o

def run_experiment(num_test=None):
    env = ThuGEnv(attack="AAD_Comprise", config_list=config_list_4o, noise_level=0) 

    if num_test is None:
        num_test = env.num_questions

    accum_reward = 0
    accum_success = 0

    agent = BaselineAgent(model="gpt-4o")
    curr_time = datetime.now().strftime("%Y%m%d-%H%M%S")
    save_msg_file = f"results/agent_messages_{curr_time}.json"
    
    for i in range(env.num_questions):
        observation, _ = env.reset(i) # first observation is question
        agent.reset()
        
        # run one episode
        for s in range(env.max_steps):
            print(f"Observation: {observation}")
            print("*"*50)
            action, submit = agent.act(observation)
            observation, reward, _, _ = env.step(action=action, submit=submit)

            if submit:
                break
        
        accum_reward += reward
        accum_success += reward == 1

        with open(save_msg_file, "w") as f:
            json.dump(agent.messages, f, indent=4)
        print(f"Question {i+1} | Reward: {reward} | Accumlated Success: {accum_success}/{i+1}")

        if i == num_test:
            print(f"Tested {num_test} questions. Stopping...")
            break


if __name__ == "__main__":
    run_experiment(num_test=5)
    