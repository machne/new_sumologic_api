from sumologic import SumoLogic
import requests
import json  # <-- ADD THIS


SUMO_ACCESS_ID = "suElwH1hUc2sfP"
SUMO_ACCESS_KEY = "tJP0UZDFtPoXuHI2Pb8rolHkZMPVjXSrNte77zi2HO09q8SHxHQaEQxiY3c47JR1"
SUMO_DEPLOYMENT = "fed" 

# Make one simple API call
auth = (SUMO_ACCESS_ID, SUMO_ACCESS_KEY)
headers = {"Content-Type": "application/json", "Accept": "application/json"}

response = requests.get(
    "https://api.fed.sumologic.com/api/sec/v1/rules",
    auth=auth,
    headers=headers,
    params={"offset": 0, "limit": 100}
)

data = response.json()

# Print the ENTIRE raw response
print("ENTIRE RAW API RESPONSE:")
print("="*60)
print(json.dumps(data, indent=2))