import requests
import pandas as pd
from datetime import datetime

SUMO_ACCESS_ID = "suElwH1hUc2sfP"
SUMO_ACCESS_KEY = "tJP0UZDFtPoXuHI2Pb8rolHkZMPVjXSrNte77zi2HO09q8SHxHQaEQxiY3c47JR1"
SUMO_DEPLOYMENT = "fed" 


def get_all_cse_rules():
    """
    Get ALL CSE rules with pagination
    """
    auth = (SUMO_ACCESS_ID, SUMO_ACCESS_KEY)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    
    all_rules = []
    offset = 0
    limit = 100  # Number of rules per page
    
    while True:
        # Add pagination parameters
        params = {
            "offset": offset,
            "limit": limit
        }
        
        print(f"Fetching page... offset: {offset}")
        
        response = requests.get(
            "https://api.fed.sumologic.com/api/sec/v1/rules",
            auth=auth,
            headers=headers,
            params=params
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Get rules from this page
        rules = data.get('data', {}).get('objects', [])
        all_rules.extend(rules)  # Add them to our list
        
        print(f"  Retrieved {len(rules)} rules (Total so far: {len(all_rules)})")
        
        # Check if there are more pages
        has_next = data.get('data', {}).get('hasNextPage', False)
        
        if not has_next:
            print("No more pages!")
            break
        
        # Move to next page
        offset += limit
    
    return all_rules

# Get all rules
print("Fetching ALL CSE rules...\n")
all_rules = get_all_cse_rules()

print(f"\n✓ Total rules retrieved: {len(all_rules)}")

# Show rule types
rule_types = [rule.get('ruleType') for rule in all_rules if rule.get('ruleType')]
unique_types = set(rule_types)
print(f"✓ Unique rule types: {sorted(unique_types)}")

print("\nCount by type:")
for rule_type in sorted(unique_types):
    count = rule_types.count(rule_type)
    print(f"  {rule_type}: {count}")