from secgym.myconfig import config_list_4o
from secgym.qagen.qa_gen import QAGen
import os
graph_files = [
    # 'incident_34.graphml',
    # 'incident_166.graphml',
    'incident_55.graphml',
    # 'incident_5.graphml',
    # 'incident_38.graphml',
    # 'incident_134.graphml',
    # 'incident_39.graphml',
    'incident_322.graphml'
 ]

include_entry = False
if include_entry:
    file_suffix = "qa_entry.json"
else:
    file_suffix = "qa.json"

for file in graph_files:
    qagenena = QAGen(
        qa_path=f"../env/questions/{file.split('.')[0]}_{file_suffix}.json",
        graph_path=os.path.join("graph_files", file),
        config_list=config_list_4o,
        cache_seed=41,
        include_entry=False,
    )
    qagenena.generate_qa()