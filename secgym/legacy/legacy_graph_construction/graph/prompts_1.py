# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A file containing prompts definition."""

GRAPH_EXTRACTION_PROMPT = """
-Goal-
Given a security report, identify all entities of those types from the text and all relationships among the identified entities.
The knowledge graph would be a connection of events happened during the attack.
Focus on how the attack events are connected and do not include any irrelevant information such as how investigations were conducted.

-Steps-
1. Identify all entities. For each identified entity, extract the following information:
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
- relationship_strength: a numeric score indicating strength of the relationship between the source entity and target entity
 Format each relationship as ("relationship"<|><source_entity><|><target_entity><|><relationship_description><|><relationship_strength>)

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

We can use the help of `Security Copilot Script Analyzer` to get some additional information.

![](images/14-Investigation-InitialAccess-PowerShell-Script-Analysis.png)

We can run the following KQL query to find `mshta` which then executes another process that makes a network connection:

```
DeviceProcessEvents
| where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
| where InitiatingProcessVersionInfoOriginalFileName == 'MSHTA.EXE'
| join kind=inner ( 
    DeviceNetworkEvents 
    | where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
    | extend ProcessId = InitiatingProcessId 
) on ProcessId
```
######################
Output:
("entity"<|>ONENOTE<|>Executable<|>OneNote is a Microsoft application used for note-taking, which in this incident was exploited to execute code)
##
("entity"<|>URUKHAI.HTA<|>File<|>Urukhai.hta is an HTA (HTML Application) file that was exported and executed by OneNote)
##
("entity"<|>MSHTA<|>Executable<|>Mshta (Microsoft HTML Application Host) is an application used to execute HTA files, which was involved in executing the Urukhai.hta file in this incident)
##
("entity"<|>POWERSHELL<|>Script<|>PowerShell is a scripting language and command-line shell, which was spawned by mshta to potentially download and execute an additional script in memory)
##
("entity"<|>192.168.3.5<|>Endpoint<|>This IP address is associated with a remote session initiated by mshta and is used for outbound connections, identified as the C2 setup for this incident)
##
("relationship"<|>ONENOTE<|>URUKHAI.HTA<|>OneNote executed code that resulted in exporting and launching the Urukhai.hta file<|>9)
##
("relationship"<|>URUKHAI.HTA<|>MSHTA<|>Urukhai.hta was launched by Mshta to further the attack<|>8)
##
("relationship"<|>MSHTA<|>POWERSHELL<|>Mshta spawned PowerShell, which was used to potentially download and execute additional scripts<|>8)
##
("relationship"<|>MSHTA<|>192.168.3.5<|>Mshta initiated a remote session with the endpoint 192.168.3.5, indicating an outbound connection to the C2 server<|>7)
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
("relationship"<|>SLIVER<|>INVOKE-DOORBREACH.PS1<|>Sliver payload was executed, which involved the Invoke-DoorBreach.ps1 script<|>6)
{completion_delimiter}
######################
Entity_types: {entity_types}
Text:
### 03 - Initial Access

Something that is not clear yet is how the `OneNote` file made it to the endpoint where the C2 connections was established.

#### OneNote File Download

Based on the parent process of `OneNote`, we can see that
it was launched by `msedge.exe` and the `OneNote` file involved was one from the `Downloads` folder: `C:\\Users\\lrodriguez\\Downloads\\FestivalDeVina.one`. We can then infer that the file was downloaded potentially from a link and executed directly from the browser.

![](images/17-Investigation-InitialAccess-OneNoteFile-Creator.png)

If we expand on the details of the file, we can see `Mark of the Web` information which tells us the URL used to download the file

![](images/18-Investigation-InitialAccess-OneNoteFile-MOW.png)

![](images/19-Investigation-InitialAccess-OneNoteFile-MOW.png)

We can then run the following query to check what process launched the browser (`msedge`) to open that specific URL and download the `OneNote` file.

```
let url = "defenderatevet06-my.sharepoint.com/personal/sbeavers_peanutrecords_com/_layouts/15/download.aspx";
DeviceEvents
| where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
| where RemoteUrl has url
```

The results shows us that the link opened in the browser originated as a link in the context of `outlook.exe`. This sounds like phishing.

![](images/20-Investigation-InitialAccess-OneNoteFile-BrowserLaunchedToOpenUrl.png)


#### Phishing Email Delivery

We can run the following query to validate that the link was clicked in the context of an email being delivered as part of a phishing campaign.

```
let url = "defenderatevet06-my.sharepoint.com/personal/sbeavers_peanutrecords_com/_layouts/15/download.aspx";
UrlClickEvents
| where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
| where Workload == 'Email'
| where ActionType == 'ClickAllowed'
| where Url has url
```

![](images/21-Investigation-InitialAccess-Outlook-UrlClickEvents-Email.png)

We can run the following query to verify the link was part of the email `body`.

```
let url = "defenderatevet06-my.sharepoint.com/personal/sbeavers_peanutrecords_com/_layouts/15/download.aspx";
UrlClickEvents
| where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
| where Workload == 'Email'
| where ActionType == 'ClickAllowed'
| where Url has url
| join kind=inner ( 
    EmailUrlInfo 
    | where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00)) 
) on NetworkMessageId
| project-reorder UrlLocation,UrlDomain,Url1
```

![](images/22-Investigation-InitialAccess-Outlook-EmailUrlInfo-Location.png)


Finally, we can run the following query to figure out who sent the phishing e-mail with the link to download a script that eventually downloads and executes a `sliver` binary.

```
EmailEvents
| where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
| where NetworkMessageId == '6e5740e4-5d51-4d17-574a-08db72e297c2'
| project-reorder SenderFromAddress,RecipientEmailAddress
```

![](images/23-Investigation-InitialAccess-Outlook-EmailInfo-Sender.png)


We can see that `sbeavers@peanutrecords.com` sent the phishing e-mail with subject `Nuevos Contactos de Festival De vina 2023!`. We can infer that `Stevie Beavers` was compromised first or it is an insider job. This explains why the sharepoint link pointed to Stevie's OneDrive (SharePoint) locations `defenderatevet06-my.sharepoint.com/personal/sbeavers_peanutrecords_com/_layouts/15/download.aspx`
######################
Output:
("entity"<|>ONENOTE<|>Executable<|>OneNote is a Microsoft application used for note-taking, which in this incident was exploited to execute code)
##
("entity"<|>MSEDGE<|>Executable<|>Msedge.exe is the Microsoft Edge web browser, which was used to download the OneNote file in this incident)
##
("entity"<|>FESTIVALDEVINA.ONE<|>File<|>FestivalDeVina.one is the OneNote file located in the Downloads folder of the user, which was downloaded and executed as part of the attack)
##
("entity"<|>FESTIVALDEVINA DOWNLOAD LINK<|>Link<|>defenderatevet06-my.sharepoint.com/personal/sbeavers_peanutrecords_com/_layouts/15/download.aspx is the URL that was clicked to download the OneNote file)
##
("entity"<|>OUTLOOK<|>Executable<|>Outlook.exe is an email client used to open the phishing email that contained the malicious link)
##
("entity"<|>SBREAVERS@PEANUTRECORDS.COM<|>Email<|>sbeavers@peanutrecords.com is the email address used to send the phishing email containing the malicious link)
##
("entity"<|>STEVIE BEAVERS<|>User<|>Stevie Beavers, associated with the email sbeavers@peanutrecords.com, whose account was used to send the phishing email)
##
("relationship"<|>ONENOTE<|>MSEDGE<|>OneNote was launched by msedge.exe<|>9)
## 
("relationship"<|>ONENOTE<|>FESTIVALDEVINA.ONE<|>OneNote was used to open the FestivalDeVina.one file<|>8)
##
("relationship"<|>MSEDGE<|>FESTIVALDEVINA DOWNLOAD LINK<|>Msedge.exe opened the Download link<|>5)
##
("relationship"<|>FESTIVALDEVINA.ONE<|>FESTIVALDEVINA DOWNLOAD LINK<|>The FestivalDeVina.one file was downloaded from the link defenderatevet06-my.sharepoint.com/personal/sbeavers_peanutrecords_com/_layouts/15/download.aspx<|>7)
##
("relationship"<|>FESTIVALDEVINA DOWNLOAD LINK<|>OUTLOOK<|>The link was clicked in the context of an email delivered through Outlook<|>6)
##
("relationship"<|>FESTIVALDEVINA DOWNLOAD LINK<|>SBREAVERS@PEANUTRECORDS.COM<|>The phishing email containing the link was sent from this email address<|>7)
##
("relationship"<|>SBREAVERS@PEANUTRECORDS.COM<|>STEVIE BEAVERS<|>The email is Stevie Beavers's account<|>5)
{completion_delimiter}
######################
Entity_types: {entity_types}
Text:

### 03 - Initial Access

Something that is not clear yet is how the `OneNote` file made it to the endpoint where the C2 connections was established.

#### OneNote File Download

Based on the parent process of `OneNote`, we can see that 
it was launched by `msedge.exe` and the `OneNote` file involved was one from the `Downloads` folder: `C:\\Users\\lrodriguez\\Downloads\\FestivalDeVina.one`. We can then infer that the file was downloaded potentially from a link and executed directly from the browser.

![](images/17-Investigation-InitialAccess-OneNoteFile-Creator.png)

If we expand on the details of the file, we can see `Mark of the Web` information which tells us the URL used to download the file

![](images/18-Investigation-InitialAccess-OneNoteFile-MOW.png)

![](images/19-Investigation-InitialAccess-OneNoteFile-MOW.png)

We can then run the following query to check what process launched the browser (`msedge`) to open that specific URL and download the `OneNote` file.

```
let url = "defenderatevet06-my.sharepoint.com/personal/sbeavers_peanutrecords_com/_layouts/15/download.aspx";
DeviceEvents
| where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
| where RemoteUrl has url
```

The results shows us that the link opened in the browser originated as a link in the context of `outlook.exe`. This sounds like phishing.

![](images/20-Investigation-InitialAccess-OneNoteFile-BrowserLaunchedToOpenUrl.png)


#### Phishing Email Delivery

We can run the following query to validate that the link was clicked in the context of an email being delivered as part of a phishing campaign.

```
let url = "defenderatevet06-my.sharepoint.com/personal/sbeavers_peanutrecords_com/_layouts/15/download.aspx";
UrlClickEvents
| where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
| where Workload == 'Email'
| where ActionType == 'ClickAllowed'
| where Url has url
```

![](images/21-Investigation-InitialAccess-Outlook-UrlClickEvents-Email.png)

We can run the following query to verify the link was part of the email `body`.

```
let url = "defenderatevet06-my.sharepoint.com/personal/sbeavers_peanutrecords_com/_layouts/15/download.aspx";
UrlClickEvents
| where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
| where Workload == 'Email'
| where ActionType == 'ClickAllowed'
| where Url has url
| join kind=inner ( 
    EmailUrlInfo 
    | where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00)) 
) on NetworkMessageId
| project-reorder UrlLocation,UrlDomain,Url1
```

![](images/22-Investigation-InitialAccess-Outlook-EmailUrlInfo-Location.png)


Finally, we can run the following query to figure out who sent the phishing e-mail with the link to download a script that eventually downloads and executes a `sliver` binary.

```
EmailEvents
| where TimeGenerated between (datetime(2023-06-22T00:00:00) .. datetime(2023-06-23T00:00:00))
| where NetworkMessageId == '6e5740e4-5d51-4d17-574a-08db72e297c2'
| project-reorder SenderFromAddress,RecipientEmailAddress
```

![](images/23-Investigation-InitialAccess-Outlook-EmailInfo-Sender.png)


We can see that `sbeavers@peanutrecords.com` sent the phishing e-mail with subject `Nuevos Contactos de Festival De vina 2023!`. We can infer that `Stevie Beavers` was compromised first or it is an insider job. This explains why the sharepoint link pointed to Stevie's OneDrive (SharePoint) locations `defenderatevet06-my.sharepoint.com/personal/sbeavers_peanutrecords_com/_layouts/15/download.aspx`.
######################
Output:
("entity"<|>FESTIVALDEVINA.ONE<|>File<|>FestivalDeVina.one is the OneNote file that was created or modified in the OneDrive of sbeavers@peanutrecords.com for further malicious purposes)
##
("entity"<|>SBREAVERS@PEANUTRECORDS.COM<|>Email<|>sbeavers@peanutrecords.com is the email address used in the context of the attack, where the OneNote file was created or uploaded in OneDrive)
##
("entity"<|>MICROSOFT ONEDRIVE FOR BUSINESS<|>Executable<|>Microsoft OneDrive for Business is a cloud storage service used in this incident to store the malicious OneNote file)
##
("entity"<|>MICROSOFT GRAPH<|>Executable<|>Microsoft Graph is an API platform used to perform operations on OneDrive, such as creating or modifying the malicious file FestivalDeVina.one)
##
("relationship"<|>FESTIVALDEVINA.ONE<|>SBREAVERS@PEANUTRECORDS.COM<|>The OneNote file was created or uploaded in the OneDrive of this account<|>3)
##
("relationship"<|>SBREAVERS@PEANUTRECORDS.COM<|>MICROSOFT ONEDRIVE FOR BUSINESS<|>Stevie Beavers's account was used to run Microsoft OneDrive for Business<|>5)
##
("relationship"<|>MICROSOFT ONEDRIVE FOR BUSINESS<|>MICROSOFT GRAPH<|>Microsoft Graph API is part of the Microsoft OneDrive for Business operations<|>4)
##
("relationship"<|>FESTIVALDEVINA.ONE<|>MICROSOFT GRAPH<|>The OneNote file was created or modified using the Microsoft Graph API<|>6)
{completion_delimiter}
######################
- Real Data -
######################
Entity_types: {entity_types}
Text: {input_text}
######################
Output:"""

CONTINUE_PROMPT = "MANY entities were missed in the last extraction.  Add them below using the same format:\n"
LOOP_PROMPT = "It appears some entities may have still been missed.  Answer YES | NO if there are still entities that need to be added.\n"
