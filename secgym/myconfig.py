from azure.identity import get_bearer_token_provider, AzureCliCredential

# aoai_endpoint = "https://medeina-openai-dev-011.openai.azure.com/"
# aoai_emb_endpoint = "https://medeinaapi-dev-openai-san.openai.azure.com/"

token_provider = get_bearer_token_provider(
    AzureCliCredential(), "https://cognitiveservices.azure.com/.default"
)

CONFIG_LIST = [
  # {
  #   "model": "gpt-4o-0513-spot",
  #   "base_url": "https://devpythiaaoaiauseast.openai.azure.com",
  #   "api_type": "azure",
  #   "api_version": "2024-08-01-preview",
  #   "tags": ["gpt-4o"],
  #   "azure_ad_token_provider": token_provider
  # },
  # {
  #   "model": "gpt-4o-0513-spot",
  #   "base_url": "https://devpythiaaoaiswedencentral.openai.azure.com",
  #   "api_type": "azure",
  #   "api_version": "2025-01-01-preview",
  #   "tags": ["gpt-4o"],
  #   "azure_ad_token_provider": token_provider
  # },
  # {
  #   "model": "gpt-4-0125-spot",
  #   "base_url": "https://devpythiaaoaicanadacentral.openai.azure.com",
  #   "api_type": "azure",
  #   "api_version": "2024-08-01-preview",
  #   "tags": ["gpt-4o"],
  #   "azure_ad_token_provider": token_provider
  # },
      {
        "model": "gemini-2.5-flash-preview-04-17",
        "api_key": open("/Users/kevin/Downloads/SecRL/googlekey").read().strip(),
        "api_type": "google",
        "tags": ["gemini-2.5-flash"],
        # "price": [0.03/1000, 0.05/1000],
    },
      {
        "model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "base_url": "https://api.deepinfra.com/v1/openai",
        "api_key": open("/Users/kevin/Downloads/SecRL/deepinfrakey").read().strip(),
        "api_type": "openai",
        "tags": ["llama3-8b"],
        "price": [0.03/1000, 0.05/1000],
    },
  {
    "model": "phi4",
    "endpoint": "https://Phi-4-secrl.eastus.models.ai.azure.com",
    "api_type": "ai_foundry",
    "tags": ["phi4"],
  },
  {
    "model": "r1",
    "endpoint" : "https://DeepSeek-R1-secrl.eastus.models.ai.azure.com",
    "api_type": "ai_foundry",
    "tags": ["r1"], 
  },
  {
    "model": "gpt-4o",
    "base_url": "https://devpythiaaoaieus2.openai.azure.com",
    "api_type": "azure",
    "api_version": "2025-01-01-preview",
    "tags": ["gpt-4o"],
    "price": [2.5/1000, 10.0/1000],
    "azure_ad_token_provider": token_provider
  },
  {
     "model": "gpt-4o-0806",
      "base_url": "https://devpythiaaoainwus3.openai.azure.com",
      "api_type": "azure",
      "api_version": "2025-01-01-preview",
      "tags": ["gpt-4o"],
      "price": [2.5/1000, 10.0/1000],
      "azure_ad_token_provider": token_provider
  },
  { #
    "model": "gpt-4.1",
    "base_url": "https://devpythiaaoaieus2.openai.azure.com",
    "api_type": "azure",
    "api_version": "2025-01-01-preview",
    "tags": ["gpt-4.1"],
    "price": [2.0/1000, 8.0/1000],
    "azure_ad_token_provider": token_provider
  },
  { #https://metabase-aoi-eus2.openai.azure.com/openai/deployments/gpt-4.1/chat/completions?api-version=2025-01-01-preview
     #https://metabase-aoi-eus2.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2025-01-01-preview
    "model": "gpt-4.1",
    "base_url": "https://metabase-aoi-eus2.openai.azure.com",
    "api_type": "azure",
    "api_version": "2025-01-01-preview",
    "tags": ["gpt-4.1"],
    "price": [2.0/1000, 8.0/1000],
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o",
    "base_url": "https://metabase-aoi-eus2.openai.azure.com",
    "api_type": "azure",
    "api_version": "2025-01-01-preview",
    "tags": ["gpt-4o"],
    "price": [2.5/1000, 10.0/1000],
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-08-01-preview",
    "tags": ["gpt-4o"],
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o-2",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-08-01-preview",
    "tags": ["gpt-4o"],
    "azure_ad_token_provider": token_provider
  },
  {
      "model": "o1-preview-2024-09-12-global",
      "base_url": "https://devpythiaaoaieus2.openai.azure.com",
      "api_type": "azure",
      "api_version": "2024-08-01-preview",
      "tags": ["o1"],
      "azure_ad_token_provider": token_provider
  },
  {
      "model": "o1-preview",
      "base_url": "https://ai-nguyenthanhai426837561304.cognitiveservices.azure.com",
      "api_type": "azure",
      "api_version": "2024-08-01-preview",
      "tags": ["o1"],
      "azure_ad_token_provider": token_provider
  },
    {
      "model": "o1-preview",
      "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
      "api_type": "azure",
      "api_version": "2024-08-01-preview",
      "tags": ["o1"],
      "azure_ad_token_provider": token_provider
  },
  {
      "model": "o1-ga-2024-12-17",
      "base_url": "https://devpythiaaoaieus2.openai.azure.com",
      "api_type": "azure",
      "api_version": "2024-12-01-preview",
      "tags": ["o1-ga"],
      "price": [15.0/1000, 60.0/1000],
      "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o-mini",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2025-01-01-preview",
    "tags": ["4o-mini"],
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o-mini-2",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2025-01-01-preview",
    "tags": ["4o-mini"],
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o-mini-3",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2025-01-01-preview",
    "tags": ["4o-mini"],
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o-mini-4",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2025-01-01-preview",
    "tags": ["4o-mini"],
    "azure_ad_token_provider": token_provider
  },
    {
    "model": "gpt-4o-mini-5",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2025-01-01-preview",
    "tags": ["4o-mini"],
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o-mini-6",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2025-01-01-preview",
    "tags": ["4o-mini"],
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o-mini-7",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2025-01-01-preview",
    "tags": ["4o-mini"],
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o-mini-8",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2025-01-01-preview",
    "tags": ["4o-mini"],
    "azure_ad_token_provider": token_provider
  },
    {
    "model": "gpt-4o-mini-9",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2025-01-01-preview",
    "tags": ["4o-mini"],
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o-mini-10",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2025-01-01-preview",
    "tags": ["4o-mini"],
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "o3-mini",
    "base_url": "https://metabase-aoi-eus2.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-12-01-preview",
    "tags": ["o3-mini"],
    "price": [1.1/1000, 4.4/1000],
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "o3-mini",
    "base_url": "https://devpythiaaoaieus2.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-12-01-preview",
    "price": [1.1/1000, 4.4/1000],
    "tags": ["o3-mini"],
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "o1-mini-2024-09-12-global",
    "base_url": "https://devpythiaaoaieus2.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-08-01-preview",
    "tags": ["o1-mini"],
    "price" : [1.1/1000, 4.4/1000], #TODO: This is wrong price, it should be [3.0/1000, 12.0/1000]
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "o1-mini-2024-09-12-standard",
    "base_url": "https://devpythiaaoaieus2.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-08-01-preview",
    "tags": ["o1-mini"],
    "price" : [1.1/1000, 4.4/1000], #TODO: This is wrong price, it should be [3.0/1000, 12.0/1000]
    "azure_ad_token_provider": token_provider
  },
  #fine-tuned models
  {
    "model": "gpt-4o-2024-08-06-secrl_cv1",
    "base_url": "https://devpythiaaoaieus2.openai.azure.com",
    "api_type": "azure",
    "api_version": "2025-01-01-preview",
    "tags": ["gpt-4o-ft-cv1"],
    "azure_ad_token_provider": token_provider
  }
]

config_list_o1 = [
    {
      "model": "o1-preview-2024-09-12-global",
      "base_url": "https://devpythiaaoaieus2.openai.azure.com",
      "api_type": "azure",
      "api_version": "2024-08-01-preview",
      "azure_ad_token_provider": token_provider
  },
  {
      "model": "o1-preview",
      "base_url": "https://ai-nguyenthanhai426837561304.cognitiveservices.azure.com",
      "api_type": "azure",
      "api_version": "2024-08-01-preview",
      "azure_ad_token_provider": token_provider
  },
    {
      "model": "o1-preview",
      "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
      "api_type": "azure",
      "api_version": "2024-08-01-preview",
      "azure_ad_token_provider": token_provider
  }
]

config_list_35 = [
  {
      "model": "gpt-35-turbo-0125",
      "base_url": "https://yroai2.openai.azure.com/",
      "api_type": "azure",
      "api_version": "2024-05-01-preview",
      "azure_ad_token_provider": token_provider,
        "price": [0.0005, 0.0015]
  }
]

config_list_4o_mini = [
  {
    "model": "gpt-4o-mini",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-08-01-preview",
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o-mini-2",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-08-01-preview",
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o-mini-3",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-08-01-preview",
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o-mini-4",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-08-01-preview",
    "azure_ad_token_provider": token_provider
  },
    {
    "model": "gpt-4o-mini-5",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-08-01-preview",
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o-mini-6",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-08-01-preview",
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o-mini-7",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-08-01-preview",
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o-mini-8",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-08-01-preview",
    "azure_ad_token_provider": token_provider
  },
    {
    "model": "gpt-4o-mini-9",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-08-01-preview",
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o-mini-10",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-08-01-preview",
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o-mini-11",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-08-01-preview",
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o-mini-12",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-08-01-preview",
    "azure_ad_token_provider": token_provider
  }
]

config_list_4o = [
  {
    "model": "gpt-4o-0513-spot",
    "base_url": "https://devpythiaaoaiauseast.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-08-01-preview",
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o-0513-spot",
    "base_url": "https://devpythiaaoaiswedencentral.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-08-01-preview",
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4-0125-spot",
    "base_url": "https://devpythiaaoaicanadacentral.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-08-01-preview",
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-08-01-preview",
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o-2",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-08-01-preview",
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o-3",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-08-01-preview",
    "azure_ad_token_provider": token_provider
  },
  {
    "model": "gpt-4o-4",
    "base_url": "https://secphibench-aoai-eastus.openai.azure.com",
    "api_type": "azure",
    "api_version": "2024-08-01-preview",
    "azure_ad_token_provider": token_provider
  },
]

# config_list_4o = [
#   {
#       "model": "gpt-4o",
#       "base_url": "https://dataoai3.openai.azure.com/",
#       "api_type": "azure",
#       "api_version":  "2024-05-01-preview",
#       "azure_ad_token_provider": token_provider,
#       "price": [0.005, 0.015]
#   },
#   {
#       "model": "gpt-4o",
#       "base_url": "https://dataoai2.openai.azure.com/",
#       "api_type": "azure",
#       "api_version":  "2024-05-01-preview",
#       "azure_ad_token_provider": token_provider,
#       "price": [0.005, 0.015]
#   },
#   {

#         "model": "gpt-4o-2024-05-13",
#         "base_url": "https://aif-complex-tasks-west-us-3.openai.azure.com/",
#         "api_type": "azure",
#         "api_version":  "2024-05-01-preview",
#         "azure_ad_token_provider": token_provider,
#   },
#     {
#       "model": "gpt-4o",
#       "base_url": "https://yadaoai.openai.azure.com/",
#       "api_type": "azure",
#       "api_version":  "2024-05-01-preview",
#       "azure_ad_token_provider": token_provider,
#       "price": [0.005, 0.015]
#   },
#       {
#       "model": "gpt-4o_2",
#       "base_url": "https://yadaoai.openai.azure.com/",
#       "api_type": "azure",
#       "api_version":  "2024-05-01-preview",
#       "azure_ad_token_provider": token_provider,
#       "price": [0.005, 0.015]
#   },
#   {
#       "model": "gpt-4o",
#       "base_url": "https://yroai.openai.azure.com/",
#       "api_type": "azure",
#       "api_version":  "2024-05-01-preview",
#       "azure_ad_token_provider": token_provider,
#       "price": [0.005, 0.015]
#   },
#   {
#       "model": "gpt-4o-2024-05-13",
#       "base_url": "https://yroai5.openai.azure.com/",
#       "api_type": "azure",
#       "api_version":  "2024-05-01-preview",
#       "azure_ad_token_provider": token_provider,
#     "price": [0.005, 0.015]
#   },
#     {
#       "model": "gpt-4o",
#       "base_url": "https://yroai2.openai.azure.com/",
#       "api_type": "azure",
#       "api_version":  "2024-05-01-preview",
#       "azure_ad_token_provider": token_provider,
#       "price": [0.005, 0.015]
#   },
# ]


config_list_4_0125 = [
    {
        "model": "gpt-4-1106-preview",
        "base_url": "https://medeina-openai-dev-011.openai.azure.com/",
        "api_type": "azure",
        "api_version":  "2023-09-15-preview",
        "azure_ad_token_provider": token_provider
    }
]

# config_list_4_0125 = [
#     {
#         "model": "gpt-4-0125-preview",
#         "base_url": "https://yroai.openai.azure.com/",
#         "api_type": "azure",
#         "api_version":  "2024-05-01-preview",
#         "azure_ad_token_provider": token_provider,
#         "price": [0.01, 0.03]
#     }
# ]

config_list_4_turbo = [
    {
        "model": "gpt-4-turbo-2024-04-09",
        "base_url": "https://yroai5.openai.azure.com/",
        "api_type": "azure",
        "api_version":  "2024-05-01-preview",
        "azure_ad_token_provider": token_provider,
        "price": [0.01, 0.03]
    }
]

config_list_4_combin = [
    {
        "model": "gpt-4-0125-preview",
        "base_url": "https://yroai.openai.azure.com/",
        "api_type": "azure",
        "api_version":  "2024-05-01-preview",
        "azure_ad_token_provider": token_provider
    },
    {
        "model": "gpt-4-turbo-2024-04-09",
        "base_url": "https://yroai5.openai.azure.com/",
        "api_type": "azure",
        "api_version":  "2024-05-01-preview",
        "azure_ad_token_provider": token_provider
    }
]

if __name__ == "__main__":

  from autogen import OpenAIWrapper
  import autogen

#   client = OpenAIWrapper(config_list=config_list_35, cache_seed=None)
#   print("Test gpt 35", client.create(messages=[{"role": "user", "content":"hello"}]).choices[0].message.content)

  #client = OpenAIWrapper(config_list=config_list_4o, cache_seed=None)
  #print("Test gpt 4o", client.create(messages=[{"role": "user", "content":"hello"}]).choices[0].message.content)

  # client = OpenAIWrapper(config_list=config_list_4o_mini, cache_seed=None)
  # print("Test gpt 4o-mini", client.create(messages=[{"role": "user", "content":"hello"}]).choices[0].message.content)

  # client = OpenAIWrapper(config_list=config_list_o1, cache_seed=None)
  # print("Test gpt 4o1", client.create(messages=[{"role": "user", "content":"hello"}]).choices[0].message.content)

  # client = OpenAIWrapper(config_list=config_list_4_0125, cache_seed=None)
  # print("Test gpt4 0125", client.create(messages=[{"role": "user", "content":"hello"}]).choices[0].message.content)

#   client = OpenAIWrapper(config_list=config_list_4_turbo, cache_seed=None)
#   print("Test gpt4 turbo", client.create(messages=[{"role": "user", "content":"hello"}]).choices[0].message.content)
  # config = autogen.filter_config(CONFIG_LIST, filter_dict={'tags': ["gpt-4o"]})

  # client = OpenAIWrapper(config_list=config, cache_seed=None)
  # print("Test gpt 4o", client.create(messages=[{"role": "user", "content":"hello"}]).choices[0].message.content)

  import autogen
  def filter_config_list(config_list, model_name):
    config_list = autogen.filter_config(config_list, {'tags': [model_name]})
    if len(config_list) == 0:
        raise ValueError(f"model {model_name} not found in the config list, please put 'tags': ['{model_name}'] in the config list to inicate this model")
    return config_list
  
  agent_config_list = filter_config_list(CONFIG_LIST, "gpt-4.1")
  client = OpenAIWrapper(config_list=agent_config_list, cache_seed=None)
  print("Test gpt 4o-mini", client.create(messages=[{"role": "user", "content":"hello what model are you?"}]).choices[0].message.content)