
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
