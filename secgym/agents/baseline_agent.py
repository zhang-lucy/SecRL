from autogen import OpenAIWrapper
from .agent_utils import sql_parser, msging
# from tenacity import retry, wait_fixed

BASE_PROMPT = """You are a security analyst. 
You need to answer a given security question by querying the database.
The logs are stored in a MySQL database, you can use SQL queries to retrieve entries as needed.
Note there are more than 20 tables in the database, so you may need to explore the schema or check example entries to understand the database structure.

Your response should always be a thought-action pair:
Thought: <your reasoning>
Action: <your SQL query>

In Thought, you can analyse and reason about the current situation, 
Action can be one of the following: 
(1) execute[<your query>], which executes the SQL query
(2) submit[<your answer>], which is the final answer to the question
"""

BASE_SUMMARY_PROMPT = """You are a security analyst. 
You need to answer a given security question by querying the database.
The logs are stored in a MySQL database, you can use SQL queries to retrieve entries as needed.
Note there are more than 20 tables in the database, so you may need to explore the schema or check example entries to understand the database structure.

Your response should always be a thought-action pair:
Thought: <your reasoning>
Action: <your SQL query>

In Thought, you can analyse and reason about the current situation, 
Action can be one of the following: 
(1) execute[<your query>], which executes the SQL query
(2) submit[<your answer>], which is the final answer to the question

When submitting an answer, please summarize key information from intermediate steps that lead to your answer.
"""

class BaselineAgent:
    def __init__(self,
                 config_list,
                 cache_seed=41,
                 max_steps=15,
                 submit_summary=False,
                 temperature=0,
                 ):
        self.config_list = config_list
        self.client = OpenAIWrapper(config_list=config_list, cache_seed=cache_seed, temperature=temperature)
        sys_prompt = BASE_SUMMARY_PROMPT if submit_summary else BASE_PROMPT
        self.messages = [{"role": "system", "content": sys_prompt}]

        self.max_steps = max_steps
        self.submit_summary = submit_summary
        self.step_count = 0

    @property
    def name(self):
        return "BaselineAgent"

    def _call_llm(self, messages):
        response = self.client.create(
            messages=messages,
        )
        return response.choices[0].message.content
        
    def act(self, observation: str):
        self._add_message(observation, role="user")
        response = self._call_llm(messages=self.messages)
        print(response)

        if self.step_count >= self.max_steps-1 and self.submit_summary:
            summary_prompt = "You have reached maximum number of steps. Please summarize your findings of key information, and sumbit them."
            self._add_message(summary_prompt, role="system")

        try:
            thought, action = response.strip().split(f"\nAction:")
            self._add_message(response.strip(), role="assistant")
        except:
            print("\nRetry Split Action:")
            thought = response.strip()
            action = self._call_llm(self.messages + [msging(f"{thought}\nAction:")])
            print(action)
            action = action.strip()
            if not "Thought" in thought:
                thought = f"Thought: {thought}"
            self._add_message(f"{thought}\nAction:{action}", role="assistant")
        
        print("*"*50)

        self.step_count += 1
        # parse the action
        parsed_action, is_code, submit = sql_parser(action)
        
        # submit = True if "submit" in thought.lower() else False
        return parsed_action, submit
    
    def get_logging(self):
        return {
            "messages": self.messages,
            "usage_summary": self.client.total_usage_summary,
        }
    
    def _add_message(self, msg: str, role: str="user"):
        self.messages.append(msging(msg, role))

    def reset(self):
        self.step_count = 0
        sys_prompt = BASE_SUMMARY_PROMPT if self.submit_summary else BASE_PROMPT
        self.messages = [{"role": "system", "content": sys_prompt}]
        self.client.clear_usage_summary()


