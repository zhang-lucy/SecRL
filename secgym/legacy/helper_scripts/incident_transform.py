
from secgym.qagen.soc_qa_gen.soc_graph import SOCGraph
socgraph = SOCGraph()

ioc0 = socgraph.add_ioc("There is an unusual addtion of credentials to an Oauth application registration.")

# Investigation 1
investigation1 = socgraph.add_investigation(
    "Check table `AuditLogs` for relevant activities.",
    from_ioc_id=ioc0
)

# IoCs from Investigation 1
ioc1_1 = socgraph.add_ioc("User: mmelndezlujn@microsoft.com", from_investigation_id=investigation1)
ioc1_2 = socgraph.add_ioc("App Name: Demo App", from_investigation_id=investigation1)

# Investigation 2
investigation2 = socgraph.add_investigation(
    "Investigate in other activities performed by the user.",
    table_name="SecurityExposureManagement",
    from_ioc_id=ioc1_1
)

# IoCs from Investigation 2
ioc2_1 = socgraph.add_ioc("Suspicious addition of OAuth app permissions to Microsoft Graph API", from_investigation_id=investigation2)

# Investigation 3
# investigation3 = socgraph.add_investigation(
#     "Check `MicrosoftGraphActivityLogs` for recent activities with this user.",
#     from_ioc_id=ioc2_1
# )

# # IoCs from Investigation 3
# ioc3_1 = socgraph.add_ioc("More IoCs to be identified",  from_investigation_id=investigation3)

# # Investigation 4
# investigation4 = socgraph.add_investigation(
#     "Check `SigninLogs` for other authentication events from the same IP address.",
#     table_name="SigninLogs",
#     kql_query="SigninLogs | where IPAddress == '72.43.121.34' | project TimeGenerated, IPAddress, UserPrincipalName, ResultType, ResultDescription, AuthenticationRequirement, ConditionalAccessStatus, ResourceDisplayName, AppDisplayName, ResourceIdentity, ClientAppUsed, RiskLevelAggregated, RiskLevelDuringSignIn, RiskState, RiskEventTypes",
#     from_ioc_id=ioc3_1
# )

# # IoCs from Investigation 4
# ioc4_1 = socgraph.add_ioc("Multiple users are authenticating from the same IP address but failed. There is one account that successfully authenticated: mvelazco@defenderatevet17.onmicrosoft.com.", from_investigation_id=investigation4)

print("Graph Nodes:")
print(socgraph.G.nodes(data=True))

print("Graph Edges:")
print(socgraph.G.edges(data=True))

socgraph.plot_custom_graph(
root=1, 
figsize=(12, 8), 
base_node_size=15000, 
max_line_length=30, 
show_plot=False,
save_figure=True,
file_path="graph_7nodes.svg"
)
# socgraph.save_to_graphml("graph.graphml")

