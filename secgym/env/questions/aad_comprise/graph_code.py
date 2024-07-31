
from secgym.qagen.soc_graph import SOCGraph
socgraph = SOCGraph()

ioc0 = socgraph.add_ioc("There is a suspicious email reading event, where the emails are read with Graph API through a previously unknown application registration.")

# Investigation 1
investigation1 = socgraph.add_investigation(
    "Check table `OfficeActivity` with Graph API's id for mail read events.",
    table_name="OfficeActivity",
    kql_query="OfficeActivity | where Operation == 'MailItemsAccessed' and AppId == '00000003-0000-0000-c000-000000000000'",
    from_ioc_id=ioc0
)

# IoCs from Investigation 1
ioc1_1 = socgraph.add_ioc("ClientAppId: bb77fe0b-52af-4f26-9bc7-19aa48854ebf", from_investigation_id=investigation1)
ioc1_2 = socgraph.add_ioc("MailboxOwnerUPN: mmelendez@DefenderATEVET17.onmicrosoft.com", additional_info="The user's mailbox who was accessed.", from_investigation_id=investigation1)

# Investigation 2
investigation2 = socgraph.add_investigation(
    "Check table `SecurityExposureManagement` to find more information about the client app with that ID.",
    table_name="SecurityExposureManagement",
    from_ioc_id=ioc1_1
)

# IoCs from Investigation 2
ioc2_1 = socgraph.add_ioc("ObjectId: 47dee0a2-d662-4664-acfa-a28bb62bdbc0", from_investigation_id=investigation2)

# Investigation 3
investigation3 = socgraph.add_investigation(
    "Check `AADServicePrincipalSignInLogs` to identify the last time this client app with `ClientAppId` was authenticated.",
    table_name="AADServicePrincipalSignInLogs",
    kql_query="AADServicePrincipalSignInLogs | where AppId == 'bb77fe0b-52af-4f26-9bc7-19aa48854ebf'",
    from_ioc_id=ioc1_1
)

# IoCs from Investigation 3
ioc3_1 = socgraph.add_ioc("IPAddress: 72.43.121.34", additional_info="The IP address where the service principal authenticated from.", from_investigation_id=investigation3)

# Investigation 4
investigation4 = socgraph.add_investigation(
    "Check `SigninLogs` for other authentication events from the same IP address.",
    table_name="SigninLogs",
    kql_query="SigninLogs | where IPAddress == '72.43.121.34' | project TimeGenerated, IPAddress, UserPrincipalName, ResultType, ResultDescription, AuthenticationRequirement, ConditionalAccessStatus, ResourceDisplayName, AppDisplayName, ResourceIdentity, ClientAppUsed, RiskLevelAggregated, RiskLevelDuringSignIn, RiskState, RiskEventTypes",
    from_ioc_id=ioc3_1
)

# IoCs from Investigation 4
ioc4_1 = socgraph.add_ioc("Multiple users are authenticating from the same IP address but failed. There is one account that successfully authenticated: mvelazco@defenderatevet17.onmicrosoft.com.", from_investigation_id=investigation4)

# Investigation 5
investigation5 = socgraph.add_investigation(
    "Check `AuditLogs` for the latest actions that have occurred to this application registration: modifications, updates, etc.",
    table_name="AuditLogs",
    kql_query="AuditLogs | mv-expand TargetResource = TargetResources | extend TargetResourceJson = parse_json(TargetResource) | where TargetResourceJson.id == '47dee0a2-d662-4664-acfa-a28bb62bdbc0'",
    from_ioc_id=ioc2_1
)

# IoCs from Investigation 5
ioc5_1 = socgraph.add_ioc("We learn that certain changes were made against the application. Specifically, new credentials were added to the application registration right before it authenticated.", from_investigation_id=investigation5)

# Investigation 6
investigation6 = socgraph.add_investigation(
    "Check other activities with the same IP address, such as Microsoft Graph API requests.",
    table_name="MicrosoftGraphActivityLogs",
    kql_query="MicrosoftGraphActivityLogs | where RequestUri endswith '/users' or RequestUri endswith '/applications' | where IPAddress == '72.43.121.34'",
    from_ioc_id=ioc3_1
)

# IoCs from Investigation 6
ioc6_1 = socgraph.add_ioc("The same IP address is making requests to the Microsoft Graph API for both users and applications.", from_investigation_id=investigation6)

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
file_path="graph_plot.png"
)
socgraph.save_to_graphml("graph.graphml")

