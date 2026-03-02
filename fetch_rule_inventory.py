import requests

def get_all_cse_rule_types(access_id, access_key, api_url):
    """
    Dynamically discover ALL CSE rule types by paginating through all rules
    Returns: dictionary with rule types and their counts
    """
    auth = (access_id, access_key)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    
    rule_types = {}
    offset = 0
    limit = 100
    
    while True:
        response = requests.get(
            api_url,
            auth=auth,
            headers=headers,
            params={"offset": offset, "limit": limit}
        )
        
        data = response.json()
        rules = data.get('data', {}).get('objects', [])
        
        for rule in rules:
            rule_type = rule.get('ruleType')
            if rule_type:
                rule_types[rule_type] = rule_types.get(rule_type, 0) + 1
                print(f"{rule_type}, count: {rule_types[rule_type]}")

        
        if not data.get('data', {}).get('hasNextPage', False):
            break
        
        offset += limit
    
    return rule_types


def get_all_cse_rules(access_id, access_key, api_url):
    """
    Get all CSE rules with their names
    """
    auth = (access_id, access_key)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    
    all_rules = []
    offset = 0
    limit = 100
    
    while True:
        response = requests.get(
            api_url,
            auth=auth,
            headers=headers,
            params={"offset": offset, "limit": limit}
        )
        
        data = response.json()
        rules = data.get('data', {}).get('objects', [])
        if offset == 0:
            total_rules = data.get('data', {}).get('total', 0)
            print(f"Total rules to fetch: {total_rules}")
        all_rules.extend(rules)
        
        if not data.get('data', {}).get('hasNextPage', False):
            break
        
        offset += limit
    
    return all_rules, total_rules


# Main script
SUMO_ACCESS_ID = "suElwH1hUc2sfP"
SUMO_ACCESS_KEY = "tJP0UZDFtPoXuHI2Pb8rolHkZMPVjXSrNte77zi2HO09q8SHxHQaEQxiY3c47JR1"
SUMO_DEPLOYMENT = "fed" 
SUMO_API_URL = "https://api.fed.sumologic.com/api/sec/v1/rules"

# Step 1: Get rule type counts
print("Getting rule types...")
rule_types = get_all_cse_rule_types(SUMO_ACCESS_ID, SUMO_ACCESS_KEY, SUMO_API_URL)
print(f"Rule types found: {rule_types}\n")

# Step 2: Get all rules
print("Getting all rules...")
all_rules, total_rules = get_all_cse_rules(SUMO_ACCESS_ID, SUMO_ACCESS_KEY, SUMO_API_URL)


# Step 3: Print rule names to screen
print("Rule Inventory:")
print("="*60)
for rule in all_rules:
    rule_name = rule.get('name', 'NO NAME')
    rule_type = rule.get('ruleType', 'NO TYPE')
    rule_id = rule.get('id', 'NO ID')
    
    print(f"{rule_type:15} | {rule_id:40} | {rule_name}")
print(f"Total rules retrieved: {len(all_rules)}\n")
print(f"Total DATA rules: {total_rules}\n")
