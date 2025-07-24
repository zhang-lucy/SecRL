# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from azure.identity import get_bearer_token_provider, AzureCliCredential
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential

# token_provider = get_bearer_token_provider(
#     AzureCliCredential(), "https://cognitiveservices.azure.com/.default"
# )

# BE SURE TO include a "tags": [<model_name>] for each dictionary in the config_list to include the model name
# We will filter out the config list passed in to only include the model that model_name in the tags is equal to qa_gen_model
# config_list = [
#     {
#         "model": "some name",
#         "tags": ["gpt-4o"]
#     },
#     {
#         "model": "some name",
#         "tags": ["gpt-3.5"]
#     }
# ]
# If qa_gen_model = "gpt-4o", the config_list for qa_gen will be only the first dictionary in the config_list
# Similarly in run_exp.py, if you set --model gpt-4o, the config_list for the agent will be only the first dictionary in the config_list


CONFIG_LIST = [
    # exmaple using openai
    #   {
    #     "model": "gpt-4.1",
    #     "api_key": open("/Users/kevin/Downloads/SecRL/keys/openaikey").read().strip(),
    #     "tags": ["gpt-4.1"],
    # }
  
  # example of using azure openai
  # {
  #   "model": "gpt-4.1-nano",
  #   "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
  #   "api_type": "azure",
  #   "api_version": "2025-01-01-preview",
  #   "tags": ["gpt-4.1-nano"],
  #   "azure_ad_token_provider": token_provider
  # },
]

if len(CONFIG_LIST) == 0:
    print("Potential Error: No config set in CONFIG_LIST, please add your config list to the CONFIG_LIST variable in secgym/myconfig.py")