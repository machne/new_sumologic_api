import os
import requests
import pandas as pd
from dotenv import load_dotenv, find_dotenv
from rich.console import Console
from sumo_cse_functions import fetch_all_rules, extract_rule_tags, fetch_rule_types
from csv_functions import clean_and_export_to_csv, normalize_rule_types_in_csv, import_csv, parse_entity_selectors
#from sumo_lap_functions import fetch_saved_searches, clean_and_export_searches
console = Console()
load_dotenv(find_dotenv())

def export_cse_rules(org_name, access_id, access_key, endpoint):
    console.log(f"Exporting CSE rules for {endpoint}...")
    api_url=endpoint+ "/sec/v1/rules"
    rules = fetch_all_rules(access_id, access_key, api_url, max_rules=None)
    
    # preprocess the rules to extract tags
    cse_rules_processed = extract_rule_tags(rules)

# send to the csv maker
    df_rules, file_rules = clean_and_export_to_csv(cse_rules_processed, 'cse_rules', org_name)
    console.log(f"✓ Completed {org_name}", style="bold green")

 # Normalize rule types in the exported CSV
    if df_rules is not None:
        df_normalized = normalize_rule_types_in_csv(df_rules)
        # Re-save with normalized values
        df_normalized.to_csv(file_rules, index=False, encoding='utf-8-sig')
        console.log(f"✓ Normalized rule types in {file_rules}", style="bold green")
    
    console.log(f"✓ Completed {org_name}", style="bold green")


def export_saved_searches(org_name, access_id, access_key, endpoint):
    print(f"Exporting saved searches for {endpoint}...")
    searches = fetch_saved_searches(org_name, access_id, access_key, endpoint)

    console.log(f"DEBUG: Type of searches: {type(searches)}")
    console.log(f"DEBUG: Number of searches: {len(searches) if searches else 0}")

    if searches:
        df_searches, file_searches = clean_and_export_to_csv(searches, 'saved_searches', org_name)
    else:
        console.log("No searches found to export", style="yellow")


def export_rules_for_tagging(org_name, access_id, access_key, endpoint):
    """
    Export simplified CSV with just: rule name, tags, isPrototype
    For easy tag management in spreadsheet
    """
    import pandas as pd
    from datetime import datetime
    
    api_url = endpoint + "/sec/v1/rules"
    rules = fetch_all_rules(access_id, access_key, api_url, max_rules=None)
    
    # Build simplified records
    simple_records = []
    
    for rule in rules:
        # Get non-MITRE tags
        all_tags = rule.get('tags', [])
        non_mitre_tags = [tag for tag in all_tags if not tag.startswith('_mitreAttack')]
        
        simple_records.append({
            'id': rule.get('id'),
            'name': rule.get('name'),
            'tags': ', '.join(non_mitre_tags),  # Comma-separated string
            'isPrototype': rule.get('isPrototype', False)
        })
    
    # Create DataFrame
    df = pd.DataFrame(simple_records)
    
    # Export
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{org_name}_rule_tags_{timestamp}.csv"
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    
    console.log(f"✓ Exported {len(df)} rules to {filename}", style="bold green")
    console.log(f"  Columns: id, name, tags, isPrototype")
    
    return filename


def import_and_update_tags(access_id, access_key, endpoint):
    """
    Import CSV and update tags and isPrototype for rules
    """
    import pandas as pd
    
    filename = input("Enter CSV filename: ").strip().strip('"').strip("'")
    
    try:
        df = pd.read_csv(filename)
        
        console.log(f"✓ Loaded {len(df)} rules from CSV", style="bold green")
        
        auth = (access_id, access_key)
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        
        results = []
        
        for idx, row in df.iterrows():
            
            rule_id = row.get('id')
            
            if pd.isna(rule_id):
                console.log(f"  ⚠ Skipping row {idx} - no ID", style="yellow")
                continue
            
            # Parse tags from comma-separated string
            tags_str = row.get('tags', '')
            if pd.isna(tags_str) or tags_str == '':
                new_tags = []
            else:
                new_tags = [tag.strip() for tag in str(tags_str).split(',') if tag.strip()]
            
            # Get isPrototype
            is_prototype = bool(row.get('isPrototype', False))
            
            # First, GET the existing rule to preserve MITRE tags and get rule type
            get_url = f"{endpoint}/sec/v1/rules/{rule_id}"
            
            try:
                get_response = requests.get(get_url, auth=auth, headers=headers)
                get_response.raise_for_status()
                existing_rule = get_response.json()
                
                # Get existing MITRE tags
                existing_tags = existing_rule.get('tags', [])
                mitre_tags = [tag for tag in existing_tags if tag.startswith('_mitreAttack')]
                
                # Combine MITRE tags + new non-MITRE tags
                combined_tags = mitre_tags + new_tags
                
                # Get rule type for update endpoint
                rule_type = existing_rule.get('ruleType')
                
                # Normalize rule type for endpoint
                if rule_type == 'first_seen':
                    rule_type = 'first-seen'
                elif rule_type == 'templated match':
                    rule_type = 'match'
                
                # Build update payload
                update_url = f"{endpoint}/sec/v1/rules/{rule_type}/{rule_id}"
                
                payload = {
                    "fields": {
                        "tags": combined_tags,
                        "isPrototype": is_prototype
                    }
                }
                
                console.log(f"Updating {row.get('name')} ({rule_id})")
                
                # PUT to update
                update_response = requests.put(
                    update_url,
                    auth=auth,
                    headers=headers,
                    json=payload
                )
                
                update_response.raise_for_status()
                
                console.log(f"  ✓ Updated tags and isPrototype", style="bold green")
                results.append(rule_id)
                
            except requests.exceptions.HTTPError as e:
                console.log(f"  ✗ HTTP Error: {e.response.status_code}", style="bold red")
                console.log(f"  Response: {e.response.text[:300]}")
            except Exception as e:
                console.log(f"  ✗ Error: {str(e)}", style="bold red")
        
        console.log(f"\n[bold green]✓ Updated {len(results)} rules[/bold green]")
        return results
        
    except Exception as e:
        console.log(f"✗ Error: {str(e)}", style="bold red")
        return []