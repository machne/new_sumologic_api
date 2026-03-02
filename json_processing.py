
import os
import json
import requests
import pandas as pd
from dotenv import load_dotenv, find_dotenv
from rich.console import Console
from sumo_cse_functions import fetch_all_rules #, extract_rule_tags, fetch_rule_types

console = Console()
load_dotenv(find_dotenv())


def export_cse_rules_json(org_name, access_id, access_key, endpoint):
    """Export rules as native JSON"""
    import json
    from datetime import datetime
    
    api_url = endpoint + "/sec/v1/rules"
    rules = fetch_all_rules(access_id, access_key, api_url, max_rules=None)
    
    # Normalize rule types (still need this for API compatibility)
    
    """
    for rule in rules:
        if rule.get('ruleType') == 'first_seen':
            rule['ruleType'] = 'first-seen'
        #elif rule.get('ruleType') == 'templated match':
            #rule['ruleType'] = 'match'
    """
    
    # Export as JSON (no tag extraction)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{org_name}_cse_rules_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)
    
    console.log(f"✓ Exported {len(rules)} rules to {filename}", style="bold green")
    return filename

def import_and_create_rules_json(access_id, access_key, endpoint, max_rules=2):
    """Import rules from JSON - no cleanup needed!"""
    import json
    
    filename = input("Enter JSON filename: ").strip().strip('"').strip("'")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            rules = json.load(f)
        
        console.log(f"✓ Loaded {len(rules)} rules from JSON", style="bold green")
        
        auth = (access_id, access_key)
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        
        all_results = []
        
        # Group by rule type
        from collections import defaultdict
        rules_by_type = defaultdict(list)
        for rule in rules:
            rules_by_type[rule.get('ruleType')].append(rule)
        
        # Process each type
        for rule_type, type_rules in rules_by_type.items():
            
            console.log(f"\n[bold cyan]Processing {len(type_rules[:max_rules])} {rule_type} rules[/bold cyan]")
            
            create_url = f"{endpoint}/sec/v1/rules/{rule_type}"
            
            for rule in type_rules[:max_rules]:
                
                # Remove fields API doesn't want
                payload_rule = {k: v for k, v in rule.items() 
                               if k not in ['id', 'ruleId', 'created', 'createdBy', 
                                          'lastUpdated', 'lastUpdatedBy', 'contentType',
                                          'parentJaskId', 'status', 'signalCount07d', 
                                          'signalCount24h']}
                
                # Add _copy to name
                payload_rule['name'] = f"{payload_rule['name']}_copy"
                
                # Wrap in fields
                payload = {"fields": payload_rule}
                
                console.log(f"Creating: {payload_rule['name']}")
                
                try:
                    response = requests.post(create_url, auth=auth, headers=headers, json=payload)
                    response.raise_for_status()
                    created = response.json()
                    
                    console.log(f"  ✓ Created {created.get('id')}", style="bold green")
                    all_results.append(created)
                    
                except Exception as e:
                    console.log(f"  ✗ Error: {str(e)}", style="bold red")
        
        console.log(f"\n[bold green]✓ Created {len(all_results)} rules[/bold green]")
        return all_results
        
    except Exception as e:
        console.log(f"✗ Error: {str(e)}", style="bold red")
        return []


def duplicate_rules_from_csv(access_id, access_key, endpoint):
    """
    Duplicate rules listed in CSV using full JSON export as source
    """
    import pandas as pd
    import json
    
    # Get CSV with rule names
    csv_filename = input("Enter CSV filename (with rule names): ").strip().strip('"').strip("'")
    
    try:
        df = pd.read_csv(csv_filename)
        
        if 'name' not in df.columns:
            console.log("✗ CSV must have 'name' column", style="bold red")
            console.log(f"  Available columns: {df.columns.tolist()}")
            return []
        
        rule_names_to_duplicate = df['name'].dropna().tolist()
        console.log(f"✓ Found {len(rule_names_to_duplicate)} rule names in CSV", style="bold green")
        
    except Exception as e:
        console.log(f"✗ Error reading CSV: {str(e)}", style="bold red")
        return []
    
    # Get JSON with full rule data
    json_filename = input("Enter JSON filename (full rule export): ").strip().strip('"').strip("'")
    
    try:
        with open(json_filename, 'r', encoding='utf-8') as f:
            all_rules = json.load(f)
        
        console.log(f"✓ Loaded {len(all_rules)} rules from JSON", style="bold green")
        
    except Exception as e:
        console.log(f"✗ Error reading JSON: {str(e)}", style="bold red")
        return []
    
    # Match rule names and duplicate
    auth = (access_id, access_key)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    
    results = []
    not_found = []
    
    for rule_name in rule_names_to_duplicate:
        
        # Find matching rule in JSON
        matching_rule = None
        for rule in all_rules:
            if rule.get('name') == rule_name:
                matching_rule = rule
                break
        
        if not matching_rule:
            console.log(f"  ⚠ Rule not found: {rule_name}", style="yellow")
            not_found.append(rule_name)
            continue
        
        # Get rule type
        rule_type = matching_rule.get('ruleType')
        
        if not rule_type:
            console.log(f"  ✗ No ruleType for: {rule_name}", style="red")
            continue
        
        # Use build_rule_payload to filter fields properly
        payload = build_rule_payload_for_duplicate(matching_rule, rule_type, name_modifier="_copy")
        
        if not payload:
            console.log(f"  ✗ Failed to build payload for: {rule_name}", style="red")
            continue
        
        # Create URL
        create_url = f"{endpoint}/sec/v1/rules/{rule_type}"
        console.log(f"DEBUG: endpoint: {create_url} for rule type {rule_type}")
        console.log(f"Duplicating: {rule_name} → {payload['fields']['name']}")
        

        console.log(f"DEBUG: Rule type: {rule_type}")
        console.log(f"DEBUG: Payload keys: {list(payload['fields'].keys())}")
        console.log(f"DEBUG: Full payload:")
        console.log(json.dumps(payload, indent=2)[:2000]) 



        try:
            response = requests.post(create_url, auth=auth, headers=headers, json=payload)
            response.raise_for_status()
            created = response.json()
            
            console.log(f"  ✓ Created {created.get('id')}", style="bold green")
            results.append({
                'original_name': rule_name,
                'new_id': created.get('id'),
                'new_name': created.get('name')
            })
            
        except requests.exceptions.HTTPError as e:
            console.log(f"  ✗ HTTP Error: {e.response.status_code}", style="bold red")
            console.log(f"  Response: {e.response.text[:10000]}")
        except Exception as e:
            console.log(f"  ✗ Error: {str(e)}", style="bold red")
    
    # Summary
    console.log(f"\n[bold green]✓ Duplicated {len(results)} rules[/bold green]")
    if not_found:
        console.log(f"[yellow]⚠ Not found: {len(not_found)} rules[/yellow]")
        for name in not_found:
            console.log(f"  - {name}", style="yellow")
    
    return results


def build_rule_payload_for_duplicate(rule_dict, rule_type, name_modifier="_copy"):
    """
    Build payload for duplication - filters to only allowed fields per type
    """
    
    # Common fields for ALL rule types
    common_fields = [
        'assetField', 'category', 'enabled', 'entitySelectors',
        'isPrototype', 'name', 'summaryExpression', 'tags'
    ]
    
    # Type-specific fields
    type_specific = {
        'threshold': [
            'description', 'countDistinct', 'countField', 'expression',
            'limit', 'score', 'stream', 'version', 'windowSize',
            'windowSizeMilliseconds', 'groupByFields'
        ],
        'match': [  # SIMPLE MATCH FIELDS ONLY
            'description', 'expression', 'score', 'stream'
        ],
        'aggregation': [
            'aggregationFunctions', 'descriptionExpression', 'groupByEntity',
            'groupByFields', 'matchExpression', 'nameExpression',
            'scoreMapping', 'stream', 'triggerExpression', 'windowSize'
        ],
        'chain': [
            'description', 'expressionsAndLimits', 'score', 'stream', 
            'windowSize', 'windowSizeMilliseconds'
        ]
    }
    
    # Get allowed fields for this rule type
    allowed = common_fields + type_specific.get(rule_type.lower(), [])
    
    # Build payload - only include allowed fields
    payload = {}
    for field in allowed:
        if field in rule_dict and rule_dict[field] is not None:
            payload[field] = rule_dict[field]
    
    # REPLACE THE ENTIRE MATCH SECTION WITH THIS:
    if rule_type.lower() == 'match':
        # Extract values from expression fields if simple fields are missing
        
        # Get score from scoreMapping if score is missing
        if 'score' not in payload or payload['score'] is None:
            score_mapping = rule_dict.get('scoreMapping', {})
            if isinstance(score_mapping, dict):
                payload['score'] = score_mapping.get('default', 5)
            else:
                payload['score'] = 5
        
        # Get description from descriptionExpression if description is missing
        if 'description' not in payload or not payload.get('description'):
            payload['description'] = rule_dict.get('descriptionExpression', '')
    
    # Modify name
    if 'name' in payload:
        payload['name'] = f"{payload['name']}{name_modifier}"
    
    return {"fields": payload}