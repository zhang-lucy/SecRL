CREATOR_PROMPT = """Given a question, please 
- For terms that have been mentioned in the given question and repeated in the answer, please do not include them as key words.
2. create a rubric based on the golden answer. For each question, you can create at most 10 points of criteria.
For each criteria, please:
- assign a score between 0 and 1. The sum of all scores should be 1.
- each point in the rubric should be a checker that can be evaluated as True or False
- each point should be concrete and objective, for example, whether a specific term is used.

Please give your response in JSON format.

Example:
Question: How did the attacker establish the C2 connection?
Golden Answer: The attacker established the C2 connection using the `Invoke-DoorBreach` script.
Your response:
{
    "key_terms" : ["Invoke-DoorBreach"],
    "rubric": [
        {
            "point": "The answer states that 'Invoke-DoorBreach' is used to establish the C2 connection.",
            "weight": 1
        }
    ]
}

Question: What process was spawned from `mshta` and what did the process do?
Golden Answer: `PowerShell` was spawned. 1. Set the execution policy to unrestriced and hides the window, 2. download the `Invode-DoorBreach.ps1` script, 3. import the downloaded script as a module, 4. Executes the `invoke-DoorBreach` function.
Your response:
{
    "key_terms" : ["PowerShell", "Invoke-DoorBreach"],
    "rubric": [
        {
            "point": "The answer states that 'PowerShell' was spawned.",
            "weight": 0.4
        },
        {
            "point": "The answer mentions that the execution policy was set to unrestricted and the window was hidden.",    
            "weight": 0.2
        },
        {
            "point": "The answer mentions that the 'Invode-DoorBreach.ps1' script was downloaded.",
            "weight": 0.2
        },
        {
            "point": "The answer mentions that the downloaded script was imported as a module.",
            "weight": 0.1
        },
        {
            "point": "The answer states that the 'Invoke-DoorBreach' function was executed.",
            "weight": 0.1
        }
    ]
}
"""


CHECKER_PROMPT = """Given a question and rubric, please evaluate the submitted answer based on the rubric. Please replay only True or False.

Example:
Question: How did the attacker establish the C2 connection?
Golden Answer: The attacker established the C2 connection using the `Invoke-DoorBreach` script.
Given Answer: use Invoke-DoorBreach
Rubric:
1. The answer states that 'Invoke-DoorBreach' is used to establish the C2 connection.
Your response:
1. The answer states that 'Invoke-DoorBreach' is used to establish the C2 connection.
True


Question: What process was spawned from `mshta` and what did the process do?
Golden Answer: `PowerShell` was spawned. 1. Set the execution policy to unrestriced and hides the window, 2. download the `Invode-DoorBreach.ps1` script, 3. import the downloaded script as a module, 4. Executes the `invoke-DoorBreach` function.
Given Answer: PowerShell was spawned. It executed the Invoke-DoorBreach function.
Rubric:
1. The answer states that 'PowerShell' was spawned.
2. The answer mentions that the execution policy was set to unrestricted and the window was hidden.
3. The answer mentions that the 'Invode-DoorBreach.ps1' script was downloaded.
4. The answer mentions that the downloaded script was imported as a module.
5. The answer states that the 'Invoke-DoorBreach' function was executed.
Your response:
1. The answer states that 'PowerShell' was spawned.
True
2. The answer mentions that the execution policy was set to unrestricted and the window was hidden.
False
3. The answer mentions that the 'Invode-DoorBreach.ps1' script was downloaded.
False
4. The answer mentions that the downloaded script was imported as a module.
False
5. The answer states that the 'Invoke-DoorBreach' function was executed.
True
"""

from textwrap import dedent
CHECKER_PROMPT = dedent("""Given a question a submitted answer, please evaluate the submitted answer to see whether it correctly answers the question without ambiguity.

If the submitted answer is an enumeration of information containing the golden answer, 
it should be considered as false. For example, if the question ask about an IP address and the submitted answer enumerates all the IP addresses in the database.

You are given:
- A question
- The golden answer
- The submitted answer
                        
Only return "True" or "False".
""" 
)