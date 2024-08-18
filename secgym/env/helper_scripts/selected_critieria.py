# selected_criteria = {
#     "schema_understanding": {
#         "name": "schema_understanding",
#         "description": "Assesses if the appropriate tables have been identified for querying based on task requirements.",
#         "accepted_values": [
#             "excellent: all relevant tables correctly identified the first time",
#             "good: relevant tables identified after one correction",
#             "fair: relevant tables identified after multiple corrections",
#             "poor: failed to identify relevant tables correctly"
#         ]
#     },
#     "accuracy": {
#         "name": "accuracy",
#         "description": "Evaluates if the final submission provides the correct answer and summarizes the investigation effectively.",
#         "accepted_values": [
#             "excellent: correct answer with complete and clear summary",
#             "good: correct answer with minor summary issues",
#             "fair: correct answer but summary contains significant issues/omissions",
#             "poor: incorrect answer or completely missing/incorrect summary"
#         ]
#     },
#     "thought_process_evaluation": {
#         "name": "thought_process_evaluation",
#         "description": "Assesses the relevance and coherence of the reasoning steps provided in the investigation.",
#         "accepted_values": [
#             "excellent",
#             "good",
#             "fair",
#             "poor"
#         ]
#     },
#     "query_quality": {
#         "name": "query_quality",
#         "description": "Evaluates the relevance and precision of the SQL queries used to gather information.",
#         "accepted_values": [
#             "highly relevant",
#             "moderately relevant",
#             "slightly relevant",
#             "irrelevant"
#         ]
#     },
#     "efficiency": {
#         "name": "efficiency",
#         "description": "Measures the total time taken to reach the correct or best possible answer.",
#         "accepted_values": [
#             "very slow",
#             "slow",
#             "average",
#             "fast"
#         ]
#     },
#     "methodology_and_execution": {
#         "name": "methodology_and_execution",
#         "description": "Evaluates the extent to which the investigation comprehensively explores the necessary database tables and schema.",
#         "accepted_values": [
#             "excellent",
#             "good",
#             "fair",
#             "poor"
#         ]
#     }
# }

selected_criteria = [
    {
        "name": "schema_understanding",
        "description": "Assesses if the appropriate tables have been identified for querying based on task requirements.",
        "accepted_values": [
            "excellent: all relevant tables correctly identified the first time",
            "good: relevant tables identified after one correction",
            "fair: relevant tables identified after multiple corrections",
            "poor: failed to identify relevant tables correctly"
        ]
    },
    {
        "name": "accuracy",
        "description": "Evaluates if the final submission provides the correct answer and summarizes the investigation effectively.",
        "accepted_values": [
            "excellent: correct answer with complete and clear summary",
            "good: correct answer with minor summary issues",
            "fair: correct answer but summary contains significant issues/omissions",
            "poor: incorrect answer or completely missing/incorrect summary"
        ]
    },
    {
        "name": "thought_process_evaluation",
        "description": "Assesses the relevance and coherence of the reasoning steps provided in the investigation.",
        "accepted_values": [
            "excellent",
            "good",
            "fair",
            "poor"
        ]
    },
    {
        "name": "query_quality",
        "description": "Evaluates the relevance and precision of the SQL queries used to gather information.",
        "accepted_values": [
            "highly relevant",
            "moderately relevant",
            "slightly relevant",
            "irrelevant"
        ]
    },
    {
        "name": "efficiency",
        "description": "Measures the total time taken to reach the correct or best possible answer.",
        "accepted_values": [
            "very slow",
            "slow",
            "average",
            "fast"
        ]
    },
    {
        "name": "methodology_and_execution",
        "description": "Evaluates the extent to which the investigation comprehensively explores the necessary database tables and schema.",
        "accepted_values": [
            "excellent",
            "good",
            "fair",
            "poor"
        ]
    }
]

import json
with open('selected_criteria.json', 'w') as f:
    json.dump(selected_criteria, f, indent=4)