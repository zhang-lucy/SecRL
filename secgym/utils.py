
import requests
from bs4 import BeautifulSoup
import re
import json
import yaml
import os
import Levenshtein
import autogen

def msging(msg, role="user"): 
    return {"role": role, "content": msg}

def get_full_question(question_dict, add_hint=False):
    if add_hint:
        return f"{question_dict.get('context', '')} {question_dict['question']} \n Here is the hint to this questions: {question_dict['hint']}".strip()
    return f"{question_dict.get('context', '')} {question_dict['question']}".strip()


def LLM_call(instruction: str, task: str, config_list: list, **args) -> str:
    client = autogen.OpenAIWrapper(
        config_list=config_list,
        cache_seed=41,
        **args
    )
    response = client.create(
        messages = [
            {'role': 'system', 'content': instruction},
            {'role': 'user', 'content': task}
        ]
    )
    return response.choices[0].message.content


def scrap_table_schema(table_name, yaml_filename, save_yaml=True):
    yaml_filename = f"data/schema/{table_name}.yaml"
    url = f"""https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/{table_name.lower()}"""

    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch the URL: {url}")
        return None
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract the description using regex
    pattern = re.compile(r'</nav><!-- <content> --><p>(.*?)</p>', re.DOTALL)
    try:
        description = pattern.findall(str(soup))[0] 
    except IndexError:
        print(f"Description not found for table: {table_name}")
        description = 'N/A'
    else:
        print(f"Description found for table: {table_name}")
        
    # Extract column details
    columns_table = soup.find('h2', id='columns').find_next('table')
    columns = []
    for row in columns_table.find('tbody').find_all('tr'):
        cells = row.find_all('td')
        column_data = {
            'Name': cells[0].text.strip(),
            'Type': cells[1].text.strip(),
            'Description': cells[2].text.strip()
        }
        columns.append(column_data)
    
    # Create the result dictionary
    result = {
        'Name': table_name,
        'InternalName': table_name,
        'Description': description,
        'Conditions': 'N/A',  # Assuming this is a static value
        'Columns': columns
    }
    
    # Convert the result to JSON
    result_json = json.dumps(result, indent=4)
    
    # save_yaml save the original HTML content to a file
    if save_yaml:
        with open(yaml_filename, 'w', encoding='utf-8') as file:
            yaml.dump(result, file, sort_keys=False, default_flow_style=False)

    return result_json


def load_yaml(yaml_filename):
    with open(yaml_filename, 'r', encoding='utf-8') as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    return data


def find_most_similar(target, strings):
    """
    Finds the most similar string to the target in the given list of strings.

    Parameters:
    - target (str): The string to compare against the list.
    - strings (list of str): The list of strings to search through.

    Returns:
    - str: The most similar string from the list.
    """
    most_similar = None
    highest_similarity = float('inf')
    
    for string in strings:
        similarity = Levenshtein.distance(target, string)
        if similarity < highest_similarity:
            highest_similarity = similarity
            most_similar = string
    
    return most_similar



if __name__ == '__main__':

    files = os.listdir('data/tables')

    for file in files:
        table_name = file.split('.')[0]
        yaml_filename = f"data/schema/{table_name}.yaml"
        result_json = scrap_table_schema(table_name, yaml_filename)
        # print(result_json)
        # data = load_yaml(yaml_filename)
        # print(data)
        # print()
    