
from secgym.qagen.soc_qa_gen.soc_graph import SOCGraph
from secgym.utils import LLM_call
from secgym.myconfig import config_list_4o
import autogen
import re
import os
from autogen import OpenAIWrapper
from textwrap import dedent
from autogen.code_utils import execute_code


CONVERT_TO_GRAPH_PROMPT = """Given a report, please convert it to a graph by writing a Python script that uses the SOCGraph class.
The graph is a bipartite graph with two types of nodes: Investigation and IoC. A SOC graph class is defined with the following methods:
- add_investigation(description: str, table_name: str=None, kql_query:str = None, additional_info:str=None, from_ioc_id=None)
    description: str - description of the investigation
    table_name: str - table used in this investigation, can be None
    kql_query: str - Kusto query used in this investigation, can be None
    additional_info: str - additional information, usually is None. The description should be a quick sentence of this investigation, if there are more information, it should be in additional_info
- add_ioc(description: str, additional_info:str=None, from_investigation_id=None)

Please start with the following code snippet:
```python
from secgym.qagen.soc_graph import SOCGraph
socgraph = SOCGraph()
```


Example
######################
Report given
######################
Given: There is a suspicious email reading event, where the emails are read with Graph API through a previously unknown application registration.
----------------------------------------------------------------------------------------------------------------------------
## Investigation 1: Check table `OfficeActivity` with Graph API's id for mail read events.
```kql
OfficeActivity
| where Operation == "MailItemsAccessed" and AppId == "00000003-0000-0000-c000-000000000000"
```
```sql
SELECT *
FROM OfficeActivity
WHERE Operation = 'MailItemsAccessed' AND AppId = '00000003-0000-0000-c000-000000000000'
```

### I1.IoC
1. ClientAppId: bb77fe0b-52af-4f26-9bc7-19aa48854ebf
2. MailboxOwnerUPN: mmelendez@DefenderATEVET17.onmicrosoft.com
   - the user's mailbox who was accessed.
######################
Reponse
######################
```python
from secgym.qagen.soc_graph import SOCGraph
socgraph = SOCGraph()

ioc0 = soc_graph.add_ioc("There is a suspicious email reading event, where the emails are read with Graph API through a previously unknown application registration.")
investigation1 = soc_graph.add_investigation(
    "Check table `OfficeActivity` with Graph API's id for mail read events.",
    table_name="OfficeActivity",
    kql_query="OfficeActivity | where Operation == 'MailItemsAccessed' and AppId == '00000003-0000-0000-c000-000000000000'",
    from_ioc_id=ioc0
)
ioc1_a1 = soc_graph.add_ioc("ClientAppId: bb77fe0b-52af-4f26-9bc7-19aa48854ebf", from_investigation_id=investigation1)
ioc2_a1 = soc_graph.add_ioc("MailboxOwnerUPN: mmelendez@DefenderATEVET17.onmicrosoft.com", additional_info="The user's mailbox where the emails are read.", from_investigation_id=investigation1)
```
######################
"""

PRINT_SAVE_GRAPH_CODE = dedent("""
print("Graph Nodes:")
print(socgraph.G.nodes(data=True))

print("Graph Edges:")
print(socgraph.G.edges(data=True))

socgraph.plot_custom_graph(
root=1, 
figsize=(14, 12), 
base_node_size=15000, 
max_line_length=30, 
show_plot=False,
save_figure=True,
file_path="{plot_file_path}"
)
socgraph.save_to_graphml("{graph_file_path}")

"""
)
class GraphConverter:

    def __init__(self, 
                 report_file_path: str, 
                 save_folder: str,
                 config_list: str) -> None:
        self.report_file_path = report_file_path
        self.save_folder = save_folder
        self.config_list = config_list

        os.makedirs(self.save_folder, exist_ok=True)
    

    def report_to_code(self):
        """Given a report, use LLM to convert it to a code that generates a graph.
        """
        with open(self.report_file_path, 'r') as f:
            report = f.read()
        
        response = LLM_call(
            task=report,
            instruction=CONVERT_TO_GRAPH_PROMPT,
            config_list=self.config_list
        )

        pattern = r'```python(.*?)```'
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1)
        else:
            return response
    
    def save_code(self, code: str):
        with open(os.path.join(self.save_folder, "graph_code.py"), 'w') as f:
            f.write(code)

    def convert(self):
        print(f"Converting report to graph...")
        code = self.report_to_code()

        additional_code = PRINT_SAVE_GRAPH_CODE.format(
            plot_file_path="graph_plot.png",
            graph_file_path="graph.graphml"
        )

        self.save_code(code+additional_code)
        print(f"############\nExecuting the following code:\n############\n{code+additional_code}\n############")

        result = execute_code(
            use_docker=False,
            filename= "graph_code.py",
            work_dir=self.save_folder,
        )

        print(f"Result:############\n{result[1]}n")
    




    
    
        
    





    
    


    

    

        