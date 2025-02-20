# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A file containing prompts definition."""

GRAPH_EXTRACTION_PROMPT = """
-Goal-
Given a security report, identify all entities of those types from the text and all relationships among the identified entities.
We are constructing a property graph, which illusrate how events happened during the attack are connected.
Focus on how the attack events are connected and do not include any irrelevant information such as how investigations were conducted.

-Steps-
1. Identify all entities, only add non-existing identities. You will be given a list of existing entities, only add new entities that are not in the list. For each identified entity, extract the following information:
- entity_name: Name of the entity, capitalized
- entity_type: One of the following types: [{entity_types}]
- entity_description: Comprehensive description of the entity's attributes and activities
Format each entity as ("entity"<|><entity_name><|><entity_type><|><entity_description>
Do not inlcude entities used in investigations, such as "Security Copilot Script Analyzer", alerts like "SUSPICIOUS SCHEDULED TASK PROCESS LAUNCHED", "SUSPICIOUS LDAP QUERIES", etc. 

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- is_directed: One event can lead to another event, so put "True" or "False" here to indicate this is one event leading to another event. If "True", it means the source entity is the cause of the target entity.
 Format each relationship as ("relationship"<|><source_entity><|><target_entity><|><relationship_description><|><is_directed>)

3. Return output in English as a single list of all the entities and relationships identified in steps 1 and 2. Use **##** as the list delimiter.

4. When finished, output <|COMPLETE|>

######################
-Examples-
######################
Entity_types: {entity_types}
Text: 
### 02 - Initial Access

#### OneNote -> HTA File

One of the first alerts in this incident is related to a `OneNote` file executing some code. It seems to be potentially part of the threat actor's initial access tradecraft.

![](images/10-Investigation-InitialAccess-OneNote-Alert.png)

We can see that the `OneNote` document exported an HTA (HTML Application) file named `Urukhai.hta` which is then launched by `mshta` (Microsoft HTML Application Host).

![](images/11-Investigation-InitialAccess-OneNote-Mshta.png)

We can run the following KQL query to find `OneNote` executing `mshta` across all endpoints:

```
DeviceProcessEvents
| where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
| where InitiatingProcessVersionInfoOriginalFileName == 'OneNote.exe'
| where ProcessVersionInfoOriginalFileName == 'MSHTA.EXE'
```

#### HTA File -> PowerShell

We can see a remote session being initiated in the context of `mshta`. We can also see `PowerShell` being spawned by `mshta`. The remote IP address is `192.168.3.5`. We know that IP address is what we used to set up our C2 so we can see the outbound connection.

![](images/12-Investigation-InitialAccess-Mshta-NetworkConnection.png)

We can see the `PowerShell` script potentially downloading an additional script and executing it in memory.

![](images/13-Investigation-InitialAccess-PowerShell-Script.png)
######################
Output:
("entity"<|>ONENOTE<|>Executable<|>OneNote is a Microsoft application used for note-taking)
##
("entity"<|>URUKHAI.HTA<|>File<|>Urukhai.hta is an HTA (HTML Application) file that was exported and executed by OneNote)
##
("entity"<|>MSHTA<|>Executable<|>Mshta (Microsoft HTML Application Host) is an application used to execute HTA files, which was involved in executing the Urukhai.hta file in this incident)
##
("entity"<|>POWERSHELL<|>Script<|>PowerShell is a scripting language and command-line shell, which was spawned by mshta to potentially download and execute an additional script in memory)
##
("entity"<|>192.168.3.5<|>Endpoint<|>This IP address is associated with a remote session initiated by mshta and is used for outbound connections, identified as the C2 setup for this incident)
##
("relationship"<|>ONENOTE<|>URUKHAI.HTA<|>OneNote executed code that exported Urukhai.hta file<|>True)
##
("relationship"<|>MSHTA<|>URUKHAI.HTA<|>Mshta launched Urukhai.hta<|>True)
##
("relationship"<|>MSHTA<|>POWERSHELL<|>Mshta spawned PowerShell, which was used to potentially download and execute additional scripts<|>True)
##
("relationship"<|>MSHTA<|>192.168.3.5<|>Mshta initiated a remote session with the endpoint 192.168.3.5, indicating an outbound connection to the C2 server<|>True)
{completion_delimiter}
######################
Entity_types: {entity_types}
Text:
### 02 - Sliver Command and Control

We can see a binary then being executed and detected as a `Sliver` payload.

![](images/15-Investigation-InitialAccess-SliverBinary.png)

We can run the following query to get more context on the `Invoke-DoorBreach` script which seems that it had to do with the new binary being executed.

```
WindowsEvent
| where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
| where Provider == 'Microsoft-Windows-PowerShell'
| where EventID == 4104
| where EventData.Path endswith "Invoke-DoorBreach.ps1"
| extend ScriptBlockText = tostring(EventData.ScriptBlockText)
```

![](images/16-Investigation-InitialAccess-SliverDownloader-PowerShellScript.png)
######################
Output:
("entity"<|>SLIVER<|>Payload<|>Sliver is a payload that was detected as being executed in this incident)
##
("entity"<|>INVOKE-DOORBREACH.PS1<|>Script<|>Invoke-DoorBreach.ps1 is a PowerShell script that was executed in this incident)
##
("relationship"<|>INVOKE-DOORBREACH.PS1<|>SLIVER<|>Invoke-DoorBreach.ps1 script spawned the Sliver payload.<|>True)
{completion_delimiter}
######################
######################
- Real Data -
######################
Entity_types: {entity_types}
Text: {input_text}
######################
Existing Entities: 
{previous_entities}
Output:"""

CONTINUE_PROMPT = "MANY entities were missed in the last extraction.  Add them below using the same format:\n"
LOOP_PROMPT = "It appears some entities may have still been missed.  Answer YES | NO if there are still entities that need to be added.\n"
