import os
import requests
import pandas as pd
from dotenv import load_dotenv, find_dotenv
from rich.console import Console

console = Console()
load_dotenv(find_dotenv())

def import_csv():
    """Import CSV with prompt"""
    filename = input("Enter CSV filename: ").strip().strip('"').strip("'")
    
    try:
        df = pd.read_csv(filename)
        console.log(f"✓ Imported {len(df)} rows", style="bold green")
        return df
    except Exception as e:
        console.log(f"✗ Error: {str(e)}", style="bold red")
        return None


def clean_value(value):
    """Clean a single value - remove NaN, None, empty strings"""
    import pandas as pd
    
    if value is None or pd.isna(value):
        return None
    if isinstance(value, str):
        if value.strip() == '' or value.lower() == 'nan':
            return None
        return value.strip()
    return value


def parse_entity_selectors(value):
    """Parse entitySelectors from CSV (likely stringified list)"""
    import json
    import pandas as pd
    
    if pd.isna(value) or value is None:
        return []
    
    if isinstance(value, str):
        try:
            # Try parsing as JSON
            return json.loads(value.replace("'", '"'))
        except:
            return []
    
    return value if isinstance(value, list) else []


def parse_tags(value):
    """Parse tags from CSV"""
    import json
    import pandas as pd
    
    if pd.isna(value) or value is None:
        return []
    
    if isinstance(value, str):
        try:
            return json.loads(value.replace("'", '"'))
        except:
            # Try splitting by comma
            return [t.strip() for t in value.split(',') if t.strip()]
    
    return value if isinstance(value, list) else []


def parse_group_by_fields(value):
    """Parse groupByFields from CSV"""
    import json
    import pandas as pd
    
    if pd.isna(value) or value is None:
        return []
    
    if isinstance(value, str):
        try:
            return json.loads(value.replace("'", '"'))
        except:
            return [value] if value else []
    
    return value if isinstance(value, list) else []


def import_and_create_threshold_rules(access_id, access_key, endpoint, max_rules=2):
    """
    Import CSV and create threshold rules (simplified version)
    """
    import pandas as pd
    
    # Import CSV
    df = import_csv()
    
    if df is None:
        return
    
    # Filter for threshold rules only
    threshold_rules = df[df['ruleType'] == 'threshold'].head(max_rules)
    
    console.log(f"Found {len(threshold_rules)} threshold rules to create")
    
    auth = (access_id, access_key)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    create_url = f"{endpoint}/sec/v1/rules/threshold"
    
    results = []
    
    for idx, row in threshold_rules.iterrows():
        
        # Build the payload with proper structure
        payload = {
            "fields": {
                # Common fields
                "assetField": clean_value(row.get('assetField')),
                "category": clean_value(row.get('category')),
                "enabled": bool(row.get('enabled', False)),
                "entitySelectors": parse_entity_selectors(row.get('entitySelectors')),
                "isPrototype": bool(row.get('isPrototype', False)),
                "name": f"{clean_value(row.get('name'))}_copy",
                "summaryExpression": clean_value(row.get('summaryExpression')),
                "tags": parse_tags(row.get('tags')),
                
                # Threshold-specific fields
                "description": clean_value(row.get('description')),
                "countDistinct": bool(row.get('countDistinct', False)),
                "countField": clean_value(row.get('countField')),
                "expression": clean_value(row.get('expression')),
                #"expression2": clean_value(row.get('expression')),
                "limit": int(row.get('limit', 0)) if pd.notna(row.get('limit')) else 0,
                "score": int(row.get('score', 0)) if pd.notna(row.get('score')) else 0,
                "stream": clean_value(row.get('stream')),
                "version": int(row.get('version', 1)) if pd.notna(row.get('version')) else 1,
                "windowSize": clean_value(row.get('windowSizeName', 'CUSTOM')),  # ← Use windowSizeName!
                "windowSizeMilliseconds": str(row.get('windowSize')) if pd.notna(row.get('windowSize')) else None,  # ← milliseconds as string
                "groupByFields": parse_group_by_fields(row.get('groupByFields'))
        }
    }
        
        # Remove None/empty fields
        payload["fields"] = {k: v for k, v in payload["fields"].items() if v is not None and v != ''}
        
        console.log(f"\nCreating: {payload['fields']['name']}")
        
        try:
            response = requests.post(
                create_url,
                auth=auth,
                headers=headers,
                json=payload
            )
            
            response.raise_for_status()
            created_rule = response.json()
            
            console.log(f"  ✓ Created {created_rule.get('id')}", style="bold green")
            results.append(created_rule)
            
        except requests.exceptions.HTTPError as e:
            console.log(f"  ✗ HTTP Error: {e.response.status_code}", style="bold red")
            console.log(f"  Response: {e.response.text[:500]}")
        except Exception as e:
            console.log(f"  ✗ Error: {str(e)}", style="bold red")
    
    console.log(f"\n✓ Created {len(results)} threshold rules", style="bold green")
    return results


# MAIN EXECUTION
if __name__ == "__main__":
    # Get credentials
    ORG = "ORG1"
    access_id = os.getenv(f"{ORG}_ACCESS_ID")
    access_key = os.getenv(f"{ORG}_ACCESS_KEY")
    endpoint = os.getenv(f"{ORG}_ENDPOINT")
    
    console.log(f"Testing threshold rule creation for {ORG}")
    
    # Run the test
    results = import_and_create_threshold_rules(access_id, access_key, endpoint, max_rules=1000)
    
    console.log("\n=== Test Complete ===")