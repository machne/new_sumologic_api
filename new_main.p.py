from sumo_cse_functions import fetch_rule_types 
import os
from sumologic import SumoLogic
from dotenv import load_dotenv, find_dotenv


ORGS = ["ORG1"]
for org in ORGS:
    sumo = SumoLogic(
        accessId=os.getenv(f"{org}_ACCESS_ID"),
        accessKey=os.getenv(f"{org}_ACCESS_KEY"),
        endpoint=os.getenv(f"{org}_ENDPOINT")
    )

    # Now use the sumo object's methods:
    print(f"\nProcessing {org}...")
    rule_types = fetch_rule_types(access_id, access_key, cse_rules_url)
    print(f"Found rule types: {rule_types}")
   