
import gymnasium as gym
import numpy as np
import datetime, json, logging, os, re
from typing import Dict, List, Tuple, Union
import docker
import mysql.connector
from datetime import datetime
from time import sleep

from secgym.utils import get_full_question
from secgym.env.evaluator import Evaluator


ATTACKS = {
    "Blitz_Ransomware" : "bliz_ransomware_qa.json",
    "AAD_Comprise": "aad_comprise/aad_comprise_qa.json",
}

def start_container(container_name):
    client = docker.from_env()
    container = client.containers.get(container_name)
    if container.status == "running":
        print(f"Container {container_name} is already running.")
        return container
    else:
        container.start()
        print(f"Restarting stopped container with ID: {container.id}...")
        sleep(3)
        return container


class ThuGEnv(gym.Env):
    def __init__(
            self,
            attack: Union[str, int],
            config_list: List[Dict] = None,
            noise_level: int = 0,
            save_file: Union[str, bool] = True,
            max_steps: int = 15,
            container_name: str = "mysql-container",
            dataset_name: str = "env_monitor_db",
            port: str = "3306",
    ):
        self.noise_level = noise_level
        self.max_steps = max_steps

        if save_file is False:
            print("Warning: No save file provided. Logging will not be saved.")
        else:
            if isinstance(save_file, bool):            
                os.makedirs("results", exist_ok=True)
                # + datetime.now().strftime("%Y%m%d%H%M%S")
                curr_time = datetime.now().strftime("%Y%m%d-%H%M%S")
                self.save_file = f"results/{attack}_noise_{noise_level}_{curr_time}.json"
            else:
                self.save_file = save_file
        print(self.save_file)

        # set up container
        self.container_name = container_name
        self.container = start_container(container_name)
        self.connection = mysql.connector.connect(
            host='localhost',
            port=port,
            user='root',
            password='admin'
        )
        if self.connection.is_connected():
            self.cursor = self.connection.cursor()
            self.cursor.execute(f"USE {dataset_name};")
        else:
            raise ValueError("Could not connect to the database.")

        # get questions
        if isinstance(attack, int):
            self.attack = list(ATTACKS.keys())[attack]
        elif isinstance(attack, str):
            self.attack = attack

        curr_path = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(curr_path, f'questions/{ATTACKS[self.attack]}'), "r") as f:
            self._all_questions = json.load(f)
            self.num_questions = len(self._all_questions)

        # saved logs
        self.step_count = 0
        self.curr_question: Union[dict, None] = None
        self.curr_trajectory = []
        self.all_logs = []

        # evaluator
        self.evaluator = Evaluator(config_list=config_list)

    def get_attack_list(self):
        """Get the list of attacks.
        """
        return list(ATTACKS.keys())
    
    def get_table_names(self):
        """Get the table names.
        """
        self.cursor.execute("SHOW TABLES;")
        return self.cursor.fetchall()   
    
    def get_schema(self, table_name: str) -> List[Dict]:
        """Get the schema of a table.
        """
        return None

    def getAllQuestions(self) -> List[dict]:
        return self._all_questions

    def get_logging(self):
        success_query_count = 0
        total_query_count = 0
        for step in self.curr_trajectory:
            if not step['info']['submit']:
                total_query_count += 1
                if step['info']['query_success']:
                    success_query_count += 1
        
        return {
            "success": self.curr_trajectory[-1]['reward'] == 1,
            "steps": self.step_count,
            "reward": self.curr_trajectory[-1]['reward'],
            "success_query_count": success_query_count,
            "total_query_count": total_query_count,
            "question": self.curr_question,
            "trajectory": self.curr_trajectory,

        }
    
    def save_logging(self):
        if self.save_file:
            with open(self.save_file, "w") as f:
                json.dump(self.all_logs, f, indent=4)


    def execute_query(self, query: str) -> Tuple[np.ndarray, bool]:
        """Execute a query and return the result.
        """
        try:
            self.cursor.execute(query)
            # print(self.cursor.column_names)
            return self.cursor.fetchall(), True
        except Exception as e:
            return f"{e.__class__.__name__}: {e.__context__}", False


    def step(self, action: str, submit=False, stringify=True) -> Tuple[np.ndarray, float, bool, Dict]:
        """Take a step in the environment.

        Args:
            action (str): The action to take. It should be a SQL query or a string that is the final answer.
            submit (bool, optional): Whether to submit the action. Defaults to False. If set, the final answer should be passed as the action.
        
        Returns:
            Tuple[np.ndarray, float, bool, Dict]: The observation, reward, done, and info.

            In info:
                - query_success (bool): Whether the query was run successfully.
                - submit (bool): Whether the action was submitted.
        """
        if self.curr_question is None:
            raise ValueError("Cannot step in the environment without resetting first.")
        
        query_success = True
        if submit:
            observation, reward, done, info = self._submit(action)
        elif self.step_count < self.max_steps:
            try: 
                self.cursor.execute(action)
                observation = self.cursor.fetchall()
                if stringify:
                    observation = str(observation)
            except Exception as e:
                observation = f"{e.__class__.__name__}: {e.__context__}"
                query_success = False

            reward = 0
            done = False
        else:
            print("Warning: Maximum steps reached. Ending the episode.")
            observation = ""
            reward = 0
            done = True
        
        self.step_count += 1
        
        info = {
            "query_success": query_success, 
            "submit": submit,
        }

        self.curr_trajectory.append(
            {
                "action": action,
                "observation": observation,
                "reward": reward,
                "done": done,
                "info": info,
            }
        )
        return observation, reward, done, info


    def reset(self, idx=None, save_log=True) -> Tuple[str, Dict]:
        """Reset the environment and return the initial observation.

        Args:
            idx (int, optional): The index of the question to reset to. Defaults to 0
        
        Returns:
            Tuple[str, Dict]: The initial observation and info.
                - observation (str): The initial observation is the question text.
                - info (Dict): The info dictionary with fields "attack" and "noise_level".
        """
        if self.curr_question:
            self.all_logs.append(self.get_logging())
            if save_log:
                self.save_logging()

        if idx is None:
            print(f"Warning: No idx provided for reset. Defaulting to 0.")
            observation =  self._all_questions[0]
        else:
            observation =  self._all_questions[idx]

        self.curr_question = observation
        self.step_count = 0
        self.curr_trajectory = []

        info = {
            "attack": self.attack,
            "noise_level": self.noise_level,
            "qid": idx
        }
    
        return get_full_question(observation), info
    
    def render(self):
        """Render the environment.
        """
        print("Cannot render the environment.")
        pass

    def close(self):
        """Close the environment.
        """
        self.connection.close()
        self.container.stop()

    def _submit(self, answer: str) -> Tuple[np.ndarray, float, bool, Dict]:
        """Submit the answer and return the result.

        Args:
            answer (str): The answer to the question.
        
        Returns:
            Tuple[np.ndarray, float, bool, Dict]: The observation, reward, done, and info.
        """

        return "", self._eval(answer), True, {}

    def _eval(self, answer: str) -> float:
        """Evaluate the answer and return the score.
        """
        return self.evaluator.checking(self.curr_question, answer)


if __name__ == "__main__":
    env = ThuGEnv(attack=1, noise_level=0)
    # print(env.get_table_names())

    query = """SELECT *
FROM OfficeActivity
WHERE Operation = 'MailItemsAccessed'
  AND AppId = '00000003-0000-0000-c000-000000000000';
"""
#     query = """SELECT *
# FROM AADServicePrincipalSignInLogs
# WHERE AppId = 'bb77fe0b-52af-4f26-9bc7-19aa48854ebf';
# """
    result, success = env.execute_query(query)
    
    print(result, len(result))