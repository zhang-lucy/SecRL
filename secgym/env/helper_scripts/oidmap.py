import pandas as pd



# with open("env/data/AppRegistrationList.csv", "r") as f:
#     app_registration_list = pd.read_csv(f, encoding='utf-8-sig')

file = "env/data/AppRegistrationList.csv"
app_registration_list = pd.read_csv(file, encoding='utf-8-sig', sep="¤")

app_data = {
    "AADCompromiseUser": "b319ee9b-da69-4112-87a1-4fc991a643d5",
    "AddPasswordApp": "e10b350f-ec14-4d12-b63f-c6f1239799ac",
    "Agentic AI Demo": "a0386463-e635-48a6-baac-d8d6853c1fe0",
    "ARTBAS-050724ek3qd1jzgp-AppReg": "a9bd6766-1d0f-4f99-9a26-df314f331926",
    "ARTBAS-050724z4gie1hd1a-AppReg": "5187eaf4-08ef-4a5b-afbb-e4bc95bcbd7b",
    "ARTBAS-0807249n7nsskxdv-AppReg": "67721230-f30d-4c66-be64-25884899fda5",
    "ARTBAS-080724v3ik9ursxg-AppReg": "6ff067c4-6d4e-403a-995c-dcd511ef0ef5",
    "ARTBAS-160224hpcp4rein6-AppReg": "daffaaea-72f7-4cd2-9938-4f4edc462e81",
    "ARTBAS-160224v7qxvc2ghd-AppReg": "1537620f-b446-4e78-abee-8f4f7c1e6e02",
    "ARTBAS-190724pleef40zad-AppReg": "b3fd7b47-1117-41ae-bf41-b11c11963b5e",
    "ARTBAS AAD App": "841dc6f7-70dd-4473-9249-5436b5e516d0",
    "ARTBAS SharePoint Upload App": "4926cfa5-8380-45af-8191-791052a6c415",
    "ATEVET17-ADO-ServiceConnection-ARM": "c7dea80f-17cc-44cb-aa7b-35d180830c41",
    "ATEVET17-Deploy": "539912e4-5cf2-4420-965d-87e2d584433d",
    "Box": "a9a011d8-25c5-4c11-81b9-86173f763520",
    "ddf": "56dcb2ed-5415-4228-bde0-4aebde1d4b01",
    "DefenderATEVET17": "01a488ce-51c0-4544-a847-3802e9d10e6d",
    "DemoApp": "e5f62392-ab0c-441b-9420-808310195b08",
    "earendil-pull": "f68dbaa6-8a4f-4387-8ace-874396ef3f7a",
    "earendilneo4j-pull": "1de7c88f-ba58-455b-8751-c964245a9c28",
    "log-analytics-access": "ddcf8ecc-4377-48ee-9f67-9b5a4ec87d5a",
    "LogAnalyticsWorkspaceReader": "57c5eb89-c8c2-4c28-8f78-ec899c007937",
    "MBTest": "3e93c186-4682-4d08-8ead-a0fa961a4a2a",
    "mmelendezlujn": "73b78d46-e2a5-49d1-b0ed-00ad6e0afa5c",
    "mmelndezlujn": "3fb11877-0e7c-4a75-a05b-734cf31611b6",
    "msdefender": "1def496c-9122-434f-94d6-ad2255352776",
    "purview-jem-databsapp": "ea48ce16-0e97-4ccf-a306-d8b0856eac4a",
    "ReadEmailEWS": "47dee0a2-d662-4664-acfa-a28bb62bdbc0",
    "spntest": "c7ff5669-577e-4bb0-adf9-68395cf76f01",
    "testSP": "9074ca4b-5844-41e6-8e35-f2634cbaa06b",
    "treesoc-client-app-atevet17": "cc111b6e-817d-4bf4-91a4-6b25b90334ca",
    "Wrapper Script": "4aaa91cf-023f-4e71-8c5e-ddde374139cf",
    "XDR-Attack-ConnectWise": "6b47a0ae-a1fc-4730-bee9-3cbb9fb3bc20"
}
print(len(app_data), len(app_registration_list))
print(app_registration_list.columns)

app_registration_list["displayName"] = app_registration_list["displayName"].str.replace('"', '')

# create new column objectID and populate with app_data
app_registration_list["objectID"] = app_registration_list["displayName"].map(app_data)

# print("AADCompromiseUser" in app_registration_list["displayName"].values)
print("displayNameÂ" in app_registration_list.columns)

app_registration_list.columns = app_registration_list.columns.str.replace('\.', '_')



print(app_registration_list.columns.str)
# Save the cleaned DataFrame to a new CSV file

app_registration_list.to_csv("env/data/AppRegistrationList.csv", index=False, sep="¤", encoding='utf-8')