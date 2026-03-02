import os
import requests
import pandas as pd
import json
from dotenv import load_dotenv, find_dotenv
from rich.console import Console

console = Console()
load_dotenv(find_dotenv())


def build_match_rule_payload(rule_dict, name_modifier="_copy"):
    """
    Build payload for simple match rules (ruleType: "match")
    Endpoint: /rules/match
    """
    
    # Build payload with SIMPLE MATCH fields
    match_fields = {
        # Common fields
        'assetField': rule_dict.get('assetField'),
        'category': rule_dict.get('category'),
        'enabled': rule_dict.get('enabled'),
        'entitySelectors': rule_dict.get('entitySelectors'),
        'isPrototype': rule_dict.get('isPrototype'),
        'name': f"{rule_dict.get('name')}{name_modifier}",
        'summaryExpression': rule_dict.get('summaryExpression'),
        'tags': rule_dict.get('tags'),
        
        # Match-specific SIMPLE fields
        'description': rule_dict.get('description'),
        'expression': rule_dict.get('expression'),
        'score': rule_dict.get('score'),
        'stream': rule_dict.get('stream'),
    }
    
    # Optional fields
    if rule_dict.get('parentJaskId'):
        match_fields['parentJaskId'] = rule_dict.get('parentJaskId')
    
    if rule_dict.get('suppressionWindowSize'):
        match_fields['suppressionWindowSize'] = rule_dict.get('suppressionWindowSize')
    
    if rule_dict.get('tuningExpressionIds'):
        match_fields['tuningExpressionIds'] = rule_dict.get('tuningExpressionIds')
    
    # Remove None values
    match_fields = {k: v for k, v in match_fields.items() if v is not None}
    
    return {"fields": match_fields}

def duplicate_match_rules():
    """
    Standalone script to duplicate ONLY match rules
    Prompts for CSV with rule names and JSON export
    """
    
    # Get credentials from .env
    org = "ORG1"
    access_id = os.getenv(f"{org}_ACCESS_ID")
    access_key = os.getenv(f"{org}_ACCESS_KEY")
    endpoint = os.getenv(f"{org}_ENDPOINT")
    
    if not all([access_id, access_key, endpoint]):
        console.log(f"✗ Missing credentials in .env for {org}", style="bold red")
        return []
    
    console.log(f"✓ Connected to {org}", style="bold green")
    
    # Get CSV with rule names
    console.print("\n[bold cyan]Step 1: CSV with rule names to duplicate[/bold cyan]")
    csv_filename = input("Enter CSV filename: ").strip().strip('"').strip("'")
    
    try:
        df = pd.read_csv(csv_filename)
        
        if 'name' not in df.columns:
            console.log("✗ CSV must have 'name' column", style="bold red")
            console.log(f"  Available columns: {df.columns.tolist()}")
            return []
        
        rule_names = df['name'].dropna().tolist()
        console.log(f"✓ Found {len(rule_names)} rule names in CSV", style="bold green")
        
    except Exception as e:
        console.log(f"✗ Error reading CSV: {str(e)}", style="bold red")
        return []
    
    # Get JSON export
    console.print("\n[bold cyan]Step 2: JSON export with full rule data[/bold cyan]")
    json_filename = input("Enter JSON filename: ").strip().strip('"').strip("'")
    
    try:
        with open(json_filename, 'r', encoding='utf-8') as f:
            all_rules = json.load(f)
        
        console.log(f"✓ Loaded {len(all_rules)} rules from JSON", style="bold green")
        
    except Exception as e:
        console.log(f"✗ Error reading JSON: {str(e)}", style="bold red")
        return []
    
    # Filter to ONLY match rules
    match_rules = [r for r in all_rules if r.get('ruleType') == 'match']
    console.log(f"Found {len(match_rules)} match rules in JSON\n")
    
    # Get name modifier
    name_modifier = input("Enter name suffix (default: _copy): ").strip() or "_copy"
    
    # Setup API
    auth = (access_id, access_key)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    create_url = f"{endpoint}/sec/v1/rules/match"
    
    console.print(f"\n[bold cyan]Creating rules at: {create_url}[/bold cyan]\n")
    
    results = []
    not_found = []
    
    for rule_name in rule_names:
        # Find matching rule
        matching_rule = next((r for r in match_rules if r.get('name') == rule_name), None)
        
        if not matching_rule:
            console.log(f"  ⚠ Not found or not a match rule: {rule_name}", style="yellow")
            not_found.append(rule_name)
            continue
        
        # Build payload
        payload = build_match_rule_payload(matching_rule, name_modifier=name_modifier)
        
        console.log(f"Creating: {rule_name} → {payload['fields']['name']}")
        
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
            console.log(f"  Response: {e.response.text[:300]}")
        except Exception as e:
            console.log(f"  ✗ Error: {str(e)}", style="bold red")
    
    # Summary
    console.print(f"\n[bold green]{'='*60}[/bold green]")
    console.print(f"[bold green]✓ Created {len(results)} match rules[/bold green]")
    
    if not_found:
        console.print(f"[yellow]⚠ Not found: {len(not_found)} rules[/yellow]")
        for name in not_found:
            console.log(f"  - {name}", style="yellow")
    
    return results


if __name__ == "__main__":
    console.print("[bold cyan]Match Rule Duplicator[/bold cyan]\n")
    results = duplicate_match_rules()