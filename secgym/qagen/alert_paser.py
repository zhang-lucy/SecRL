
import json
import pandas as pd


# extract the latest security alerts
def extract_alert(alert_ids, security_alert):
    found_alert_ids = []
    alerts_to_return = []
    for alert in security_alert.iterrows():
        if alert[1]['SystemAlertId'] in alert_ids and alert[1]['SystemAlertId'] not in found_alert_ids:
            alerts_to_return.append(alert[1])
            found_alert_ids.append(alert[1]['SystemAlertId'])
    return alerts_to_return

def filter_incidents(security_incident):
    security_incident["TimeGenerated [UTC]"] = pd.to_datetime(security_incident["TimeGenerated [UTC]"])
    security_incident = security_incident.sort_values(by="TimeGenerated [UTC]", ascending=False)

    filtered_incidents = []
    existing_alerts = []
    existing_labels = []
    for i, incident in security_incident.iterrows():
        labels = json.loads(incident['Labels'])
        # check if the incident is the latest in one line
        is_latest = any([label['labelName'] == 'LATEST' for label in labels])
        if not is_latest:
            continue
        
        current_alerts = set(json.loads(incident['AlertIds']))
        current_labels = set([label['labelName'] for label in labels])
        # check if current alert set is already in existing alerts
        max_inter = 0
        for existing_alert in existing_alerts:
            inter = len(current_alerts.intersection(existing_alert))
            if inter > max_inter:
                max_inter = inter
        if max_inter >= 3:
            continue

        if current_labels not in existing_labels:
            filtered_incidents.append(incident)
            existing_alerts.append(current_alerts)
            existing_labels.append(current_labels)
            
    return filtered_incidents


def processs_incidents(alert_path, incident_path):
    """

    Args:
        alert_path: path to the alert csv file
        incident_path: path to the incident csv file
    
    Returns:

    """
    security_alert = pd.read_csv(alert_path)
    security_incident = pd.read_csv(incident_path)

    filtered_incidents = filter_incidents(security_incident)
    filtered_incidents = [incident for incident in filtered_incidents if incident['TimeGenerated [UTC]'] > pd.Timestamp(2024, 8, 1)]
    print(f"Number of filtered incidents: {len(filtered_incidents)}")

    incident_alert_pairs = []
    for incident in filtered_incidents:
        alert_ids = json.loads(incident['AlertIds'])
        alerts = extract_alert(alert_ids, security_alert)
        incident_alert_pairs.append((incident, alerts))
    return incident_alert_pairs


if __name__ == "__main__":
    from secgym.qagen.alert_graph import AlertGraph

    ia_pairs = processs_incidents(alert_path="./SecurityAlert.csv", incident_path="./SecurityIncident.csv")
    sample_incident, sample_alerts = ia_pairs[1]
    alert_graph = AlertGraph()
    alert_graph.build_graph_from_incident_alert(sample_incident, sample_alerts)
