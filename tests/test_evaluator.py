import json
from secgym.env.evaluator import LLMEvaluator

with open("/Users/kevin/Downloads/SecRL/secgym/agent_experiment_logs/base_agent_experiments_4o/alert_level/incident_5_agent_log_gpt-4o_46_alert.json", "r") as f:
    agent_log = json.load(f)


config_list = [
    {
        "model": "gpt-4o",
        "api_key": open("/Users/kevin/Desktop/AutoStates/key.txt", "r").read(),
    }
]

evaluator = LLMEvaluator(
    config_list=config_list, ans_check_reflection=False, sol_check_reflection=False)


question = agent_log[1]['question_dict']
answer = "vnevado-win13t.vnevado.alpineskihouse.co"
eval_dit = evaluator.checking(question, answer, eval_step=True)

print(eval_dit)

print(eval_dit['reward'])