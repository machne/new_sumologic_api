import requests
import json
import pandas as pd
from datetime import datetime

# Sumo Logic CSE API Configuration
SUMO_ACCESS_ID = "suElwH1hUc2sfP"
SUMO_ACCESS_KEY = "tJP0UZDFtPoXuHI2Pb8rolHkZMPVjXSrNte77zi2HO09q8SHxHQaEQxiY3c47JR1"
SUMO_DEPLOYMENT = "fed"  

API_ENDPOINT = "https://api.fed.sumologic.com/api/sec/v1/rules"

def get_cse_rules():
    """
    Retrieve all CSE rules from Sumo Logic
    """
    
    auth = (SUMO_ACCESS_ID, SUMO_ACCESS_KEY)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(
            API_ENDPOINT,
            auth=auth,
            headers=headers
        )
        
        response.raise_for_status()
        data = response.json()
        
        print("Raw API Response:")
        print(json.dumps(data, indent=2))
        
        return data
        
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    except Exception as err:
        print(f"An error occurred: {err}")
        return None

if __name__ == "__main__":
    data = get_cse_rules()