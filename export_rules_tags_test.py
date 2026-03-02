import os
import re
from sumologic import SumoLogic
from dotenv import load_dotenv, find_dotenv
import pandas as pd
from datetime import datetime
from rich.console import Console

# Initialize console for rich logging
console = Console()
console.log('Loading Environment Variables...')
load_dotenv(find_dotenv())


def download_rules_inventory(access_id, access_key, api_url, rule_types_list, org_name):
    try:   # Create filename with customer name and current timestamp
        
        sumo = SumoLogic(access_id, access_key, api_url)
        
        query = ""  # No filtering criteria

        # Get rules from the API
        console.log(f"Retrieving Rules for {org_name}...")
        cse_rules = sumo.get_cse_rules(query_string=query, types=rule_types_list)
        if not cse_rules:
            console.log(f"No rules found for {org_name}")
            #continue
        else: console.log('Got the rules!')    
        console.log('Building DataFrame...')
        df = pd.DataFrame(cse_rules)
        console.log(f'Got {df.count} rules!')

    except Exception as e:
        console.log(f"Error processing {org_name}: {str(e)}", style="bold red")