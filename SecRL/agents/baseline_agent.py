from .agent_utils import call_llm, sql_parser, msging
import json
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
                 model="gpt-4o"):
        self.model = model
        self.messages = [{"role": "system", "content": BASE_PROMPT}]

    def act(self, observation: str):
        self.add_message(observation, role="user")
        response = call_llm(model=self.model, messages=self.messages)
        print(response)

        try:
            thought, action = response.strip().split(f"\nAction:")
            self.add_message(response.strip(), role="assistant")
        except:
            print("\nRetry Split Action:")
            thought = response.strip()
            action = call_llm(self.model, self.messages + [msging(f"{thought}\nAction:")])
            print(action)
            action = action.strip()
            if not "Thought" in thought:
                thought = f"Thought: {thought}"
            self.add_message(f"{thought}\nAction:{action}", role="assistant")
        
        print("*"*50)
        parsed_action, is_code, submit = sql_parser(action)
        
        # submit = True if "submit" in thought.lower() else False
        return parsed_action, submit
    
    def add_message(self, msg: str, role: str="user"):
        self.messages.append(msging(msg, role))

    def reset(self):
        self.messages = [{"role": "system", "content": BASE_PROMPT}]


