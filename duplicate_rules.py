import os
import requests
import pandas as pd
import json
from dotenv import load_dotenv, find_dotenv
from rich.console import Console

console = Console()
load_dotenv(find_dotenv())






def build_rule_payload(rule_dict, rule_type, name_modifier="_copy"):
    
    
    
    
    """
    Build payload for any rule type based on Sumo's official templates
    """
    
    # Common fields for ALL rule types
    common_fields = {
        'assetField': rule_dict.get('assetField'),
        'category': rule_dict.get('category'),
        'enabled': rule_dict.get('enabled'),
        'entitySelectors': rule_dict.get('entitySelectors'),
        'isPrototype': rule_dict.get('isPrototype'),
        'name': f"{rule_dict.get('name')}{name_modifier}",
        'summaryExpression': rule_dict.get('summaryExpression'),
        'tags': rule_dict.get('tags'),
    }
    
    # Type-specific fields based on rule type
    if rule_type == 'match':
        specific_fields = {
            'description': rule_dict.get('description'),
            'expression': rule_dict.get('expression'),
            'score': rule_dict.get('score'),
            'stream': rule_dict.get('stream'),
        }
    
    elif rule_type == 'templated match':
        specific_fields = {
            'descriptionExpression': rule_dict.get('descriptionExpression'),
            'expression': rule_dict.get('expression'),
            'nameExpression': rule_dict.get('nameExpression'),
            'scoreMapping': rule_dict.get('scoreMapping'),
            'stream': rule_dict.get('stream'),
        }
    
    elif rule_type == 'threshold':
        specific_fields = {
            'countDistinct': rule_dict.get('countDistinct'),
            'countField': rule_dict.get('countField'),
            'description': rule_dict.get('description'),
            'expression': rule_dict.get('expression'),
            'groupByFields': rule_dict.get('groupByFields'),
            'limit': rule_dict.get('limit'),
            'score': rule_dict.get('score'),
            'stream': rule_dict.get('stream'),
            'version': rule_dict.get('version'),
            'windowSize': rule_dict.get('windowSizeName'),  # Use enum name
            'windowSizeMilliseconds': rule_dict.get('windowSize'),  # Milliseconds
        }
    
    elif rule_type == 'chain':
        # Clean expressionsAndLimits - remove 'index' field
        expressions_and_limits = rule_dict.get('expressionsAndLimits', [])
        if expressions_and_limits:
            cleaned_expressions = []
            for expr in expressions_and_limits:
                cleaned_expressions.append({
                    'expression': expr.get('expression'),
                    'limit': expr.get('limit')
                })
            expressions_and_limits = cleaned_expressions
        
        specific_fields = {
            'description': rule_dict.get('description'),
            'expressionsAndLimits': expressions_and_limits,
            'groupByFields': rule_dict.get('groupByFields'),
            'ordered': rule_dict.get('ordered'),
            'score': rule_dict.get('score'),
            'stream': rule_dict.get('stream'),
            'windowSize': rule_dict.get('windowSizeName'),  # ← Use enum name
            'windowSizeMilliseconds': str(rule_dict.get('windowSize')) if rule_dict.get('windowSize') else None,  # ← String
    }
    
    elif rule_type == 'aggregation':
        specific_fields = {
            'aggregationFunctions': rule_dict.get('aggregationFunctions'),
            'descriptionExpression': rule_dict.get('descriptionExpression'),
            'groupByAsset': rule_dict.get('groupByAsset'),
            'groupByFields': rule_dict.get('groupByFields'),
            'matchExpression': rule_dict.get('matchExpression'),
            'nameExpression': rule_dict.get('nameExpression'),
            'scoreMapping': rule_dict.get('scoreMapping'),
            'stream': rule_dict.get('stream'),
            'triggerExpression': rule_dict.get('triggerExpression'),
            'windowSize': rule_dict.get('windowSizeName'),  # ← Use enum name
            'windowSizeMilliseconds': str(rule_dict.get('windowSize')) if rule_dict.get('windowSize') else None,  # ← String
    }
    
    elif rule_type == 'outlier':
        specific_fields = {
            'nameExpression': rule_dict.get('nameExpression'),
            'groupByFields': rule_dict.get('groupByFields'),
            'score': rule_dict.get('score'),
            'baselineWindowSize': rule_dict.get('baselineWindowSize'),
            'retentionWindowSize': rule_dict.get('retentionWindowSize'),
            'floorValue': rule_dict.get('floorValue'),
            'deviationThreshold': rule_dict.get('deviationThreshold'),
            'descriptionExpression': rule_dict.get('descriptionExpression'),
            'matchExpression': rule_dict.get('matchExpression'),
            'aggregationFunctions': rule_dict.get('aggregationFunctions'),
            'windowSize': rule_dict.get('windowSizeName'),  # ← Use enum name
            'windowSizeMilliseconds': str(rule_dict.get('windowSize')) if rule_dict.get('windowSize') else None,  # ← String
    }

    elif rule_type == 'first seen':
        specific_fields = {
            'descriptionExpression': rule_dict.get('descriptionExpression'),
            'nameExpression': rule_dict.get('nameExpression'),
            'filterExpression': rule_dict.get('filterExpression'),
            'valueFields': rule_dict.get('valueFields'),
            'valueExpression': rule_dict.get('valueExpression'),
            'groupByFields': rule_dict.get('groupByFields'),
            'score': rule_dict.get('score'),
            'version': rule_dict.get('version'),
            'baselineWindowSize': rule_dict.get('baselineWindowSize'),
            'retentionWindowSize': rule_dict.get('retentionWindowSize'),
            'baselineType': rule_dict.get('baselineType'),
        }


    else:
        console.log(f"  ⚠ Unsupported rule type: {rule_type}", style="yellow")
        return None
    
    # Merge common + specific
    all_fields = {**common_fields, **specific_fields}
    
    # Optional common fields
    if rule_dict.get('parentJaskId'):
        all_fields['parentJaskId'] = rule_dict.get('parentJaskId')
    
    if rule_dict.get('suppressionWindowSize'):
        all_fields['suppressionWindowSize'] = rule_dict.get('suppressionWindowSize')
    
    if rule_dict.get('tuningExpressionIds'):
        all_fields['tuningExpressionIds'] = rule_dict.get('tuningExpressionIds')
    
    # Remove None values
    all_fields = {k: v for k, v in all_fields.items() if v is not None}
    
    return {"fields": all_fields}


def duplicate_rules(rule_type_filter=None):
    """
    Generic rule duplicator - works for any rule type
    
    Args:
        rule_type_filter: Optional - only duplicate this type (e.g., 'match', 'threshold')
    """
    
    # Get credentials
    org = "ORG1"
    access_id = os.getenv(f"{org}_ACCESS_ID")
    access_key = os.getenv(f"{org}_ACCESS_KEY")
    endpoint = os.getenv(f"{org}_ENDPOINT")
    
    if not all([access_id, access_key, endpoint]):
        console.log(f"✗ Missing credentials", style="bold red")
        return []
    
    # Endpoint mapping
    endpoint_map = {
        'match': 'match',
        'templated match': 'templated',
        'threshold': 'threshold',
        'chain': 'chain',
        'aggregation': 'aggregation',
        'first seen': 'first-seen',
        'outlier': 'outlier'
    }
    
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
    
    # Filter by type if specified
    if rule_type_filter:
        all_rules = [r for r in all_rules if r.get('ruleType') == rule_type_filter]
        console.log(f"Filtered to {len(all_rules)} {rule_type_filter} rules")
    
    # Get name modifier
    name_modifier = input("\nEnter name suffix (default: _copy): ").strip() or "_copy"
    
    # Setup
    auth = (access_id, access_key)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    
    results = []
    
    for rule_name in rule_names:
        # Find rule
        matching_rule = next((r for r in all_rules if r.get('name') == rule_name), None)
        
        if not matching_rule:
            console.log(f"  ⚠ Not found: {rule_name}", style="yellow")
            continue
        
        rule_type = matching_rule.get('ruleType')
        
        # Get endpoint
        rule_endpoint = endpoint_map.get(rule_type)
        if not rule_endpoint:
            console.log(f"  ⚠ Unknown type {rule_type}: {rule_name}", style="yellow")
            continue
        
        # Build payload
        payload = build_rule_payload(matching_rule, rule_type, name_modifier)
        if not payload:
            continue
        
        create_url = f"{endpoint}/sec/v1/rules/{rule_endpoint}"
        
        console.log(f"Creating [{rule_type}]: {rule_name}")
        
        try:
            response = requests.post(create_url, auth=auth, headers=headers, json=payload)
            response.raise_for_status()
            created = response.json()
            
            console.log(f"  ✓ {created.get('id')}", style="bold green")
            results.append(created)
            
        except requests.exceptions.HTTPError as e:
            console.log(f"  ✗ HTTP {e.response.status_code}", style="bold red")
            console.log(f"  {e.response.text[:200]}")
        except Exception as e:
            console.log(f"  ✗ {str(e)}", style="bold red")
    
    console.log(f"\n✓ Created {len(results)} rules", style="bold green")
    return results


if __name__ == "__main__":
    # Can filter by type or do all
    # results = duplicate_rules(rule_type_filter='match')  # Only match
    results = duplicate_rules()  # All types