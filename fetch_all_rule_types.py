import requests

def get_all_cse_rule_types(access_id, access_key):
    """
    Dynamically discover ALL CSE rule types by paginating through all rules
    Returns: sorted list of unique rule type strings
    """
    auth = (access_id, access_key)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    
    rule_types = set()
    offset = 0
    limit = 100
    
    while True:
        response = requests.get(
            "https://api.fed.sumologic.com/api/sec/v1/rules",
            auth=auth,
            headers=headers,
            params={"offset": offset, "limit": limit}
        )
        
        data = response.json()
        rules = data.get('data', {}).get('objects', [])
        
        # Collect rule types from this page
        for rule in rules:
            rule_type = rule.get('ruleType')
            if rule_type:
                rule_types.add(rule_type)
        
        # Check if more pages exist
        if not data.get('data', {}).get('hasNextPage', False):
            break
        
        offset += limit
    
    return sorted(rule_types)


# Usage
SUMO_ACCESS_ID = "suElwH1hUc2sfP"
SUMO_ACCESS_KEY = "tJP0UZDFtPoXuHI2Pb8rolHkZMPVjXSrNte77zi2HO09q8SHxHQaEQxiY3c47JR1"
SUMO_DEPLOYMENT = "fed" 

all_types = get_all_cse_rule_types(SUMO_ACCESS_ID, SUMO_ACCESS_KEY)
print(f"Discovered rule types: {all_types}")