import os
from secgym.qagen.graph_converter import GraphConverter
from secgym.qagen.qa_generator import QAGenerator
from secgym.myconfig import config_list_4o


save_folder = "./env/questions/aad_comprise_test"
report_file_path="./qagen/aad_comprise_report.txt"


# 1. Convert the report to graph
graph_converter = GraphConverter(
    report_file_path=report_file_path,
    save_folder=save_folder,
    config_list=config_list_4o
)

graph_converter.convert()


# 2. Generate question from the graph
graphml_file = os.path.join(save_folder, "graph.graphml")
config_list = []

qa_generator = QAGenerator(
    graphml_file=graphml_file,
    question_file=os.path.join(save_folder, "aad_comprise_qa.json"),
    config_list=config_list_4o
)
questions_dict = qa_generator.generate_questions()
print(questions_dict)
