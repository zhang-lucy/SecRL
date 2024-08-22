import pandas as pd
from secgym.qagen.alert_paser import processs_incidents
from secgym.qagen.alert_graph import AlertGraph


# ia_pairs = processs_incidents(alert_path="./SecurityAlert.csv", incident_path="./SecurityIncident.csv")
# sample_incident, sample_alerts = ia_pairs[1]
# alert_graph = AlertGraph()
# alert_graph.build_graph_from_incident_alert(sample_incident, sample_alerts)
# alert_graph.incident

alert_graph = AlertGraph()
alert_graph.load_graph_from_graphml("sample_incident.graphml")
print("Alert graph loaded.")

# alert_graph.plot_custom_graph(
#     save_figure=True,
#     file_path="sample_incident.png",
#     figsize=(40, 40),
#     show_plot=False
# )
# print("Alert graph plotted.")

# alert_graph.get_e2e_paths()
# alert_graph.get_graph_patterns()
alert_graph.get_alert_paths()