"""
https://github.com/lamini-ai/lamini/blob/86bcbec07b340cf0cdf2b5804923592d58d70f57/llama/docs_to_qa/docs_to_qa.py
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Union
from collections import defaultdict
import os
import re
import json

import pandas as pd
from openai import AzureOpenAI
from tqdm import tqdm

from myconfig import config_list
from autogen import OpenAIWrapper

class QAGenerator(BaseModel):
    """
    Params:
        config_list (List[dict]): A list of LLM configs, refer to AuoGen for more details.
        docs (Dict[str, str]): A dictionary of document IDs and their corresponding text.
        n_questions (int): The number of question-answer pairs to generate per document.

        question_answer_system_prompt (str): The prompt to guide the AI in generating question-answer pairs.
        fewshot_examples: Examples constructed of Doc + QAs.

    Attributes:
        cache_seed (Union[int, None]): A seed to use for caching, if None, no caching is used, refer to AuoGen for more details.
        client (autogen.OpenAIWrapper): An instance of the AutoGen's OpenAIWrapper class.
        questions (Dict[str, List[str]]): A dictionary to store generated question-answer pairs, keyed by document ID.
    """
    # autogen parameters
    config_list: List[dict] = None
    cache_seed: Union[int, None] = None
    client: OpenAIWrapper = None

    # LLM prompts

# Criteria for questions:
# - Your question should always require the agent to query the data, not just some reasoning or testing their knowledge.
# - But do not ask questions that just queries the data. Form the questions that requires analyse the tables.
# - Try to frame the question to be clear and specific, and have a easy way to verify the answer. 
# - The question should require some kind of judgement or reasoning of what to try and query based on the context to answer the question.

    question_answer_system_prompt: str = """You are a senior security analyst that will give questions answer pairs based on a investigation report for a simulated attack. Your questions and answers should be based on the given text. 
Basic test setup:
An attack is simulated in the environment. All logs in a certain time range are collected. This includes more that 20 tables.
The agent has access to all the tables and can query them using Kusto Query Language (KQL). 

Now your goal is to generate questions and answers based on the given text. These questions should be designed to test the agent's ability to retrieve relevant information from tables, their knowledge in security, and their ability to analyze the data.
Since it is hard to answer questions such as "when does the attack happens" using the raw logs, we may give certain background information/context when asking one question.
The idea is to give the agent some context from one part of the report, and the maybe take the next part as the ground truth and ask some questions based on that.
"""
    fewshot_examples: str = None

    # qa generation
    qaformat: str = "txt"
    docs: Dict[str, str] = Field(default_factory=dict)
    n_questions: int = 5
    questions: Dict[str, List[str]] = Field(default_factory=lambda: defaultdict(list))

    class Config:
        arbitrary_types_allowed = True


    def __init__(self, **data):
        super().__init__(**data)

        if self.qaformat == "json":
            self.client = OpenAIWrapper(config_list=self.config_list, cache_seed=self.cache_seed, response_format={ "type": "json_object" })
            self.question_answer_system_prompt += "Please generate questions and answers in JSON format."
        else:
            self.client = OpenAIWrapper(config_list=self.config_list, cache_seed=self.cache_seed)
            # self.question_answer_system_prompt += "Please generate questions in this format: <i>. Context: <context> Question: <question>  Answer: <answer> Golden_Query: <golden_query>\nNote that context and golden_query are optional. Golden query is also part of the answer."
            self.question_answer_system_prompt += "Please generate questions in this format: <i>. Context: <context> Question: <question>  Answer: <answer>\nNote that context is optional"

        if self.fewshot_examples:
            self.question_answer_system_prompt += "Here are examples of generated questions:\n" + self.fewshot_examples
    
    @staticmethod 
    def format_fewshot(fewshot_doc, fewshot_qas: dict, qaformat="json"):
        returned_str = f"<REFERENCE TEXT>\n{fewshot_doc}</REFERENCE TEXT>\n\n"
        if qaformat == "json":
            tmp_js = {}
            for i in range(len(fewshot_qas)):
                tmp_js[i] = fewshot_qas[i]
            returned_str += json.dumps(fewshot_qas, indent=4)
        else:
            for i, qa in enumerate(fewshot_qas):
                returned_str += f"{i}. Context: {qa['context']} Question: {qa['question']} Answer: {qa['answer']}\n\n" #  Golden_Query: {qa['golden_query']}
        print(returned_str)
        return returned_str
    
    def _make_prompt(self, system_prompt, user_prompt):
        return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]

    def _parse_llm_output(self, output):
        output = output.choices[0].message.content
        print("raw_output", output)
        if self.qaformat == "json":
            try: 
                output = json.loads(output)
                return output
            except Exception as e:
                print(f"Error: {e}")
                return [output]
        else:
            # split by i. "1."
            output = re.split(r"\n\d+\. ", output)
            output = output[1:]
            print("output", output)
            # put in json, remove Question: and Answer:
            
            dict_output = []
            for i in range(len(output)):
                try: 
                    context, restpart = output[i].split("Question: ")
                    question, restpart = restpart.split("Answer: ")
                except Exception as e:
                    print(output[i])
                    print("--------------")
                    continue
                # answer, restpart = restpart.split("Golden_Query: ")
                # golden_query = restpart.strip()
                dict_output.append(
                    {
                        'context': context.replace("Context: ", "").strip(),
                        'question': question.strip(),
                        'answer': restpart.strip(),
                        # 'golden_query': golden_query.strip()
                    }
                )
            return dict_output


    def generate_questions(
            self,
            save=False,
            verbose=False,
        ):
            for doc_name in self.docs:
                user_prompt = f"Please generate 1-{self.n_questions}(at most {self.n_questions}) based on the context length. Do not generate too many if they are asking about the same thing.\n\n <REFERENCE TEXT>\n{self.docs[doc_name]}</REFERENCE TEXT>\n\n1. "
                messages = self._make_prompt(self.question_answer_system_prompt, user_prompt)
                # print(self.question_answer_system_prompt)
                # exit(1)
                output = self.client.create(
                    messages=messages,
                )
                output = self._parse_llm_output(output)
                print(f"Generated {len(output)} questions for {doc_name}")
                self.questions[doc_name] = output
                    
                if save:
                    self._save_questions(doc_id=doc_name, user_prompt=user_prompt, verbose=verbose)
    

    def _save_questions(self, doc_id, user_prompt, verbose=True):
        dirpath = f"outputs/{doc_id}"
        os.makedirs(dirpath, exist_ok=True)
        filepath = f"{dirpath}/questions.json"
        with open(filepath, 'w') as f:
            json.dump(self.questions[doc_id], f, indent=4)
        if verbose:
            print(f"Saved questions for {doc_id} to {filepath}")

        prompt_filepath = f"{dirpath}/questions_prompt.json"
        with open(prompt_filepath, "w") as file:
            json.dump(
                {
                    "system_prompt": self.question_answer_system_prompt,
                    "user_prompt": user_prompt,
                },
                file,
                indent=4
            )
        if verbose:
            print(f"Saved question prompt to {prompt_filepath}")


if __name__ == "__main__":
    docs = {}
    for i in range(2, 11):
        docs[str(i)] = open(f"blitz/{i}.txt").read()

    docs["0"] = open("ransomware.txt").read()
    fewshot_doc = open("blitz/1.txt").read()
    fewshot_qas = [
    {
        "context": "One of the first alerts in an incident report is related to a `ONENOTE.EXE` file executing some code. It seems to be potentially part of the threat actor's initial access tradecraft.",  
        "question":  "Can you find the relevant log(s) and analyze what happened?",
        "answer": "We can see that the `OneNote` document exported an HTA (HTML Application) file named `Urukhai.hta` which is then launched by `mshta` (Microsoft HTML Application Host).",
    },

     {
        "context": "We can see that a `OneNote` document exported an `HTA` (HTML Application) file named `Urukhai.hta` which is then launched by `mshta` (Microsoft HTML Application Host).",  
        "question": "What process was spawned from `mshta` and what did the process do?",
        "answer": "`PowerShell` was spawned. 1. Set the execution policy to unrestriced and hides the window, 2. download the `Invode-DoorBreach.ps1` script, 3. import the downloaded script as a module, 4. Executes the `invoke-DoorBreach` function.",
     },

    {
        "context": "We found a Silver command and control (C2) connection established.",
        "question": "How did the attacker establish the C2 connection?",
        "answer":"The attacker established the C2 connection using the `Invoke-DoorBreach` script.",
    },
    {
        "context": "We found an suspicious `Invoke-DoorBreach` script executed in the PowerShell logs.",
        "question": "Can you investigate with the evidence, and find what C2 (command and control) connection was used?",
        "answer":"The Sliver command and control (C2) connection was established.",
    },
        # {
        #     "context": "One of the first alerts in an incident is related to a `OneNote` file executing some code. It seems to be potentially part of the threat actor's initial access tradecraft.",  
        #     "question":  "Can you find the relevant log(s) and analyze what happened?",
        #     "answer": "We can see that the `OneNote` document exported an HTA (HTML Application) file named `Urukhai.hta` which is then launched by `mshta` (Microsoft HTML Application Host).",
        #     # "golden_query": ""
        # },
        # {
        #     "context": "One of the first alerts in this incident was related to a `OneNote` file executing some code, which seems to be potentially part of the threat actor's initial access tradecraft.",
        #     "question": "What process was spawned from the code and what did the process do?",
        #     "answer": "`PowerShell` was spawned. We can see the PowerShell script potentially downloading an additional script and executing it in memory.",
        #     # "golden_query": ""
        # },
#         {
#             "context": "We can see a remote session being initiated in the context of `mshta`. We can also see PowerShell being spawned by mshta. ",
#             "question": "What process is used to connection to the attacker's server?",
#             "answer": "Execute the golden query to find the process that makes a network connection.",
# #             "golden_query": """
# # DeviceProcessEvents
# # | where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
# # | where InitiatingProcessVersionInfoOriginalFileName == 'MSHTA.EXE'
# # | join kind=inner ( 
# #     DeviceNetworkEvents 
# #     | where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
# #     | extend ProcessId = InitiatingProcessId 
# # ) on ProcessId"""
#         },



        # {
        #     "question": "When does the event happened?",
        #     "answer": "It started at `2023-06-22 05:39:51 UTC`."
        # },
        # {
        #     "question": "What is the suspicious activity that happens first? What user does it impact?",
        #     "answer": "A suspicious LDAP query on `workstation8.peanutrecords.com`, impacting user `lrodriguez`."
        # },
        # {
        #     "question": "What is the initial access possibly gained via?",
        #     "answer": "OneNote."
        # }
    ]

    fewshot_examples = QAGenerator.format_fewshot(fewshot_doc, fewshot_qas, qaformat="txt")
    qa_generator = QAGenerator(
        config_list=config_list,
        docs=docs, 
        fewshot_examples=fewshot_examples,
        n_questions=4
    )
    qa_generator.generate_questions(verbose=True, save=True)
