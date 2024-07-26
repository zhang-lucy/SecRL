

from env.ThuGEnv import ThuGEnv
from agents.baseline_agent import BaselineAgent
import json

def run_experiment():
    env = ThuGEnv(attack="AAD_Comprise")

    accum_reward = 0
    accum_success = 0

    agent = BaselineAgent(model="gpt-4o")
    save_msg_file = "results/agent_messages.json"
    
    for i in range(env.num_questions):
        observation, _ = env.reset(i) # first observation is question
        agent.reset()

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



if __name__ == "__main__":
    run_experiment()
    