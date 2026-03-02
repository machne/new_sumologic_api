import os
import requests
import pandas as pd
import json
from dotenv import load_dotenv, find_dotenv
from rich.console import Console
from sumo_rule_payload_builder import (
    build_rule_create_update_payload, 
    build_rule_override_payload,
    get_rule_endpoint,
    is_sumo_native_rule
)

console = Console()
load_dotenv(find_dotenv())


def manage_rule_tags():
    """
    Update tags and isPrototype for rules
    Handles both custom rules (update) and Sumo native rules (override)
    
    CSV format: name, tags (comma-separated), isPrototype
    JSON: Full rule inventory for lookups
    """
    
    # Get credentials
    org = "ORG1"
    access_id = os.getenv(f"{org}_ACCESS_ID")
    access_key = os.getenv(f"{org}_ACCESS_KEY")
    endpoint = os.getenv(f"{org}_ENDPOINT")
    
    if not all([access_id, access_key, endpoint]):
        console.log(f"✗ Missing credentials", style="bold red")
        return []
    
    console.log(f"✓ Connected to {org}", style="bold green")
    
    # Get CSV with changes
    console.print("\n[bold cyan]Step 1: CSV with changes[/bold cyan]")
    console.print("Required columns: name, tags (comma-separated), isPrototype")
    csv_filename = input("Enter CSV filename: ").strip().strip('"').strip("'")
    
    try:
        df = pd.read_csv(csv_filename)
        
        required_cols = ['name', 'tags', 'isPrototype']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            console.log(f"✗ CSV missing columns: {missing_cols}", style="bold red")
            console.log(f"  Available columns: {df.columns.tolist()}")
            return []
        
        console.log(f"✓ Loaded {len(df)} rules from CSV", style="bold green")
        
    except Exception as e:
        console.log(f"✗ Error reading CSV: {str(e)}", style="bold red")
        return []
    
    # Get JSON inventory for lookups
    console.print("\n[bold cyan]Step 2: JSON inventory (for rule IDs, types, and MITRE tags)[/bold cyan]")
    json_filename = input("Enter JSON filename: ").strip().strip('"').strip("'")
    
    try:
        with open(json_filename, 'r', encoding='utf-8') as f:
            all_rules = json.load(f)
        
        console.log(f"✓ Loaded {len(all_rules)} rules from JSON", style="bold green")
        
        # Build lookup dict by name
        rules_by_name = {rule.get('name'): rule for rule in all_rules}
        
    except Exception as e:
        console.log(f"✗ Error reading JSON: {str(e)}", style="bold red")
        return []
    
    # Setup API
    auth = (access_id, access_key)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    
    results = []
    not_found = []
    overrides = []
    updates = []
    
    console.print(f"\n[bold cyan]Processing rules...[/bold cyan]\n")
    
    for idx, row in df.iterrows():
        
        rule_name = row.get('name')
        
        if pd.isna(rule_name):
            console.log(f"  ⚠ Skipping row {idx} - no name", style="yellow")
            continue
        
        # Find rule in inventory
        inventory_rule = rules_by_name.get(rule_name)
        
        if not inventory_rule:
            console.log(f"  ⚠ Not found: {rule_name}", style="yellow")
            not_found.append(rule_name)
            continue
        
        # Get rule details
        rule_id = inventory_rule.get('id')
        rule_type = inventory_rule.get('ruleType')
        
        # Get endpoint
        rule_endpoint = get_rule_endpoint(rule_type)
        if not rule_endpoint:
            console.log(f"  ⚠ Unknown type {rule_type}: {rule_name}", style="yellow")
            continue
        
        # Parse new tags from CSV (comma-separated)
        new_tags_str = row.get('tags', '')
        if pd.isna(new_tags_str) or new_tags_str == '':
            new_non_mitre_tags = []
        else:
            new_non_mitre_tags = [tag.strip() for tag in str(new_tags_str).split(',') if tag.strip()]
        
        # Get existing MITRE tags from inventory (preserve them)
        existing_tags = inventory_rule.get('tags', [])
        mitre_tags = [tag for tag in existing_tags if tag.startswith('_mitreAttack')]
        
        # Combine MITRE tags + new non-MITRE tags
        combined_tags = mitre_tags + new_non_mitre_tags
        
        # Get isPrototype
        is_prototype = bool(row.get('isPrototype', False))
        
        # Modify the inventory rule with new values
        modified_rule = inventory_rule.copy()
        modified_rule['tags'] = combined_tags
        modified_rule['isPrototype'] = is_prototype
        
        # Determine if this is Sumo native (override) or custom (update)
        is_native = is_sumo_native_rule(rule_id)
        
        if is_native:
            # Build override payload and URL
            update_url = f"{endpoint}/sec/v1/rules/{rule_endpoint}/{rule_id}/override"
            payload = build_rule_override_payload(modified_rule, rule_type)
            operation = "Override"
            overrides.append(rule_name)
        else:
            # Build regular update payload and URL
            update_url = f"{endpoint}/sec/v1/rules/{rule_endpoint}/{rule_id}"
            payload = build_rule_create_update_payload(modified_rule, rule_type, name_modifier="")
            operation = "Update"
            updates.append(rule_name)
        
        if not payload:
            console.log(f"  ✗ Failed to build payload for {rule_name}", style="red")
            continue
        
        console.log(f"{operation}: {rule_name} ({rule_id})")
        console.log(f"  Tags: {len(combined_tags)} total ({len(mitre_tags)} MITRE + {len(new_non_mitre_tags)} custom)")
        console.log(f"  isPrototype: {is_prototype}")
        
        try:
            response = requests.put(update_url, auth=auth, headers=headers, json=payload)
            response.raise_for_status()
            
            console.log(f"  ✓ {operation} successful", style="bold green")
            results.append(rule_name)
            
        except requests.exceptions.HTTPError as e:
            console.log(f"  ✗ HTTP Error: {e.response.status_code}", style="bold red")
            console.log(f"  Response: {e.response.text[:300]}")
        except Exception as e:
            console.log(f"  ✗ Error: {str(e)}", style="bold red")
    
    # Summary
    console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
    console.print(f"[bold green]✓ Processed {len(results)} rules successfully[/bold green]")
    console.print(f"  • Overrides (Sumo native): {len(overrides)}")
    console.print(f"  • Updates (custom rules): {len(updates)}")
    
    if not_found:
        console.print(f"\n[yellow]⚠ Not found: {len(not_found)} rules[/yellow]")
        for name in not_found[:10]:
            console.log(f"  - {name}", style="yellow")
        if len(not_found) > 10:
            console.print(f"  ... and {len(not_found) - 10} more")
    
    return results


if __name__ == "__main__":
    console.print("[bold cyan]Rule Tag & Prototype Manager[/bold cyan]")
    console.print("Handles both custom rules (update) and Sumo native rules (override)\n")
    results = manage_rule_tags()