from autogen import OpenAIWrapper
from .agent_utils import sql_parser, msging

BASE_PROMPT = """You are a security analyst. 
You need to answer a given security question by querying the database.
The logs are stored in a MySQL database, you can use SQL queries to retrieve entries as needed.
Note there are more than 20 tables in the database, so you may need to explore the schema or check example entries to understand the database structure.

Your repsone should always be a thought-action pair:
Thought: <your reasoning>
Action: <your SQL query>

Thought can reason about the current situation, and Action can be two types: 
(1) execute[<your query>], which executes the SQL query: 
(2) submit[<your answer>], which indicates that the previous observation is the answer
"""



class BaselineAgent:
    def __init__(self,
                 config_list,
                 cache_seed=41,
                 ):
        self.config_list = config_list
        self.client = OpenAIWrapper(config_list=config_list, cache_seed=cache_seed)
        self.messages = [{"role": "system", "content": BASE_PROMPT}]

    def _call_llm(self, messages):
        response = self.client.create(
            messages=messages,
        )
        return response.choices[0].message.content
        
    def act(self, observation: str):
        self._add_message(observation, role="user")
        response = self._call_llm(messages=self.messages)
        print(response)

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
        self.messages = [{"role": "system", "content": BASE_PROMPT}]
        self.client.clear_usage_summary()


