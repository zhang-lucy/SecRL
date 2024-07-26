import msticpy as mp
from httpx import HTTPStatusError
# Internal Server Error
# HTTPStatusError Server error '500 Internal Server Error' for url 'https://api.security.microsoft.com/api/advancedhunting/run'
# For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/500
mdatp_prov = mp.QueryProvider("M365D")

mdatp_prov.connect()
query_string = """MicrosoftGraphActivityLogs
| take 10"""

try:
    data = mdatp_prov.exec_query(query= query_string)
except HTTPStatusError as e:
    print("caught an HTTPError")
    print(e)
else:
    print(type(data))
    print(f"'{data}'")
