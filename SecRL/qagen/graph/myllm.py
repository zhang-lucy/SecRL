from typing import Any
from azure.identity import DefaultAzureCredential, get_bearer_token_provider, AzureCliCredential
from autogen import OpenAIWrapper
from typing_extensions import Unpack

# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""LLM Types."""

from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class LLMOutput(Generic[T]):
    """The output of an LLM invocation."""

    output: T | None
    """The output of the LLM invocation."""

    json: dict | None = field(default=None)
    """The JSON output from the LLM, if available."""

    history: list[dict] | None = field(default=None)
    """The history of the LLM invocation, if available (e.g. chat mode)"""


# aoai_endpoint = "https://medeina-openai-dev-011.openai.azure.com/"
# aoai_emb_endpoint = "https://medeinaapi-dev-openai-san.openai.azure.com/"

token_provider = get_bearer_token_provider(
    AzureCliCredential(), "https://cognitiveservices.azure.com/.default"
)


# config_list = [
#   {
#       "model": "gpt-4-turbo-2024-04-09",
#       "base_url": "https://medeina-openai-dev-011.openai.azure.com/",
#       "api_type": "azure",
#       "api_version": "2023-09-15-preview",
#       "max_tokens": 1000,
#       "azure_ad_token_provider": token_provider
#   }
# ]

config_list = [
  {
      "model": "gpt-4o",
      "base_url": "https://gcrgpt4aoai8c.openai.azure.com/",
      "api_type": "azure",
      "api_version": "2023-09-15-preview",
      "azure_ad_token_provider": token_provider
  }
]

# class myllm:
#     def __init__(self):
#         self.client = OpenAIWrapper(config_list=config_list)

#     def __call__(self, *args: Any, **kwds: Any) -> Any:
#         pass

async def call_autogen(
        input,
        name=None,
        history=[],
        variables={},
        model_parameters={},
):
    formatted_input = input.format(**variables)
    # print(formatted_input)
    # replace variables in input 
    client = OpenAIWrapper(config_list=config_list)

    messages = [
        *history,
        {"role": "user", "content": formatted_input},
    ]

    model_parameters['cache_seed'] = None
    completion = client.create(messages=messages, **model_parameters)
    return LLMOutput(
        output=completion.choices[0].message.content,
        json=None,
        history=messages)
