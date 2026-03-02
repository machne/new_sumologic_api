import requests
import json
from datetime import datetime
from rich.console import Console

console = Console()
console.log('Loading Environment Variables...')

import requests
import pandas as pd
from datetime import datetime
from csv_functions import clean_and_export_to_csv, import_csv, clean_value, parse_entity_selectors, parse_tags, parse_score_mapping, parse_list_field,parse_group_by_fields
from dotenv import load_dotenv, find_dotenv

def fetch_saved_searches(org_name, access_id, access_key, endpoint):

    auth = (access_id, access_key)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    
    # Content search endpoint
    #api_url = f"{endpoint}/v2/content/folders/global/search"
    api_url = f"{endpoint}/v1/logSearches"
    print(f"DEBUG: Making request to {api_url} {endpoint}, orgname {org_name} with auth={auth}")
    
    response = requests.get(
        api_url,
        auth=auth,
        headers=headers)
    
    print(f"Status: {response.status_code}")
    print("\nFull Response:")
    print(json.dumps(response.json(), indent=2))
    print(f"API= {api_url}")

    response.raise_for_status()
    data = response.json()
    
    # Filter for just saved searches (itemType = "Search")
    saved_searches  = data.get('logSearches', [])
    #saved_searches = [item for item in all_items if item.get('itemType') == 'Search']
    
    console.log(f"Found {len(saved_searches)} saved searches out of {len(saved_searches)} total items")
    
    return saved_searches

def export_saved_searches(org_name, access_id, access_key, endpoint):
    print(f"Exporting saved searches for {endpoint}...")
    searches = fetch_saved_searches(org_name, access_id, access_key, endpoint)

    console.log(f"DEBUG: Type of searches: {type(searches)}")
    console.log(f"DEBUG: Number of searches: {len(searches) if searches else 0}")

    if searches:
        df_searches, file_searches = clean_and_export_to_csv(searches, 'saved_searches', org_name)
    else:
        console.log("No searches found to export", style="yellow")
