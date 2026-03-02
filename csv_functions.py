import json
from datetime import datetime
from rich.console import Console

import requests
import pandas as pd
from datetime import datetime
console = Console()
console.log('Loading Environment Variables...')

def clean_and_export_to_csv(data, data_type, org_name):
    """
    Generic function to clean and export any Sumo data to CSV
    
    Args:
        data: List of dictionaries (rules, searches, etc.)
        data_type: String descriptor (e.g., 'cse_rules', 'saved_searches')
        org_name: Organization name for filename
    
    Returns:
        DataFrame and filename
    """
    
    # Check if we have data
    if not data:
        console.log(f"No {data_type} to export", style="yellow")
        return None, None
    
 # DEBUG - See what we're getting
    #console.log(f"DEBUG: Type of data: {type(data)}")
    #console.log(f"DEBUG: Length: {len(data)}")
    #if len(data) > 0:
        #console.log(f"DEBUG: First item type: {type(data[0])}")
        #console.log(f"DEBUG: First item keys: {data[0].keys() if isinstance(data[0], dict) else 'Not a dict'}")
        #console.log(f"DEBUG: First item sample: {str(data[0])[:200]}")





    #console.log(f"Converting {len(data)} {data_type} to DataFrame...")
    df = pd.json_normalize(data)
    

    #console.log(f"DEBUG: DataFrame shape: {df.shape}")
    #console.log(f"DEBUG: DataFrame columns: {df.columns.tolist()[:10]}")  # First 10 columns
    #console.log(f"DEBUG: First row sample:\n{df.head(1)}")




    # Clean column names
    df.columns = df.columns.str.replace('[^a-zA-Z0-9_]', '_', regex=True)
    df.columns = df.columns.str.replace('__+', '_', regex=True)
    df.columns = df.columns.str.strip('_')
    
    # Clean string columns
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str)
            df[col] = df[col].str.replace('\n', ' ', regex=False)
            df[col] = df[col].str.replace('\r', ' ', regex=False)
            df[col] = df[col].str.replace('\t', ' ', regex=False)
            df[col] = df[col].str.replace('  +', ' ', regex=True)
            df[col] = df[col].str.strip()
    
    # sort columns alphabetically
    df = df.reindex(sorted(df.columns), axis=1)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{org_name}_{data_type}_{timestamp}.csv"
    
    # Export to CSV
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    
    console.log(f"Exported {len(df)} {data_type} to {filename}", style="bold green")
    
    return df, filename




"""Import CSV and clean NaN values"""

def import_csv():
    filename = input("Enter CSV filename: ").strip().strip('"').strip("'")
    console.log(f"Importing from {filename}...")
    try:
        df = pd.read_csv(filename)
        
        # Replace NaN with None, then drop None columns when converting to dict
        df = df.where(pd.notna(df), None)
        console.log(f"✓ Imported {len(df)} rows", style="bold green")
        return df
        
    except Exception as e:
        console.log(f"✗ Error: {str(e)}", style="bold red")
        return None
    

def get_rule_types_from_csv(filename=None):
    """
    Scan CSV and return list of unique rule types
    
    Args:
        filename: Path to CSV file (if None, prompts user)
    
    Returns:
        List of unique rule type strings, or None if error
    """
    import pandas as pd
    
    # Prompt for filename if not provided
    if filename is None:
        filename = input("Enter CSV filename: ").strip().strip('"').strip("'")
    
    try:
        # Read CSV
        df = pd.read_csv(filename)
        
        # Check if ruleType column exists
        if 'ruleType' not in df.columns:
            console.log("✗ CSV does not have 'ruleType' column", style="bold red")
            console.log(f"  Available columns: {df.columns.tolist()}")
            return None
        
        # Get unique rule types
        rule_types = df['ruleType'].dropna().unique().tolist()
        
        # Get counts per type
        type_counts = df['ruleType'].value_counts().to_dict()
        
        console.log(f"✓ Found {len(rule_types)} unique rule types:", style="bold green")
        for rule_type in sorted(rule_types):
            count = type_counts.get(rule_type, 0)
            console.log(f"  • {rule_type}: {count} rules")
        
        return rule_types
        
    except FileNotFoundError:
        console.log(f"✗ File not found: {filename}", style="bold red")
        return None
    except Exception as e:
        console.log(f"✗ Error reading CSV: {str(e)}", style="bold red")
        return None
    

def normalize_rule_types_in_csv(df):
    """
    Normalize ruleType values in DataFrame to match API endpoint names
    
    Args:
        df: DataFrame with ruleType column
    
    Returns:
        DataFrame with normalized ruleType values
    """
    
    if 'ruleType' not in df.columns:
        console.log("⚠ No ruleType column found", style="yellow")
        return df
    
    # Mapping of CSV values to API endpoint values
    normalization_map = {
        'first_seen': 'first-seen',
        'first seen': 'first-seen',
        'templated match': 'match'
    }
    
    # Count changes for logging
    changes = {}
    
    for old_value, new_value in normalization_map.items():
        count = (df['ruleType'] == old_value).sum()
        if count > 0:
            df.loc[df['ruleType'] == old_value, 'ruleType'] = new_value
            changes[old_value] = (new_value, count)
    
    # Log changes
    if changes:
        console.log("✓ Normalized rule types:", style="bold green")
        for old, (new, count) in changes.items():
            console.log(f"  • '{old}' → '{new}' ({count} rules)")
    else:
        console.log("No rule type normalization needed")
    
    return df

def clean_value(value):
    """
    Clean a single value - remove NaN, None, empty strings
    
    Args:
        value: Any value from CSV/DataFrame
    
    Returns:
        Cleaned value or None
    """
    
    # Check for None or NaN
    if value is None or pd.isna(value):
        return None
    
    # Clean strings
    if isinstance(value, str):
        # Remove if empty or "nan" string
        if value.strip() == '' or value.lower() == 'nan':
            return None
        # Return trimmed string
        return value.strip()
    
    # Return as-is for other types (int, bool, list, dict, etc.)
    return value

def parse_group_by_fields(value):
    """
    Parse groupByFields from CSV (handles stringified lists)
    
    Args:
        value: Value from CSV (could be string, list, or NaN)
    
    Returns:
        List of field names, or empty list
    """
    import json
    import pandas as pd
    
    # Return empty list for None/NaN
    if pd.isna(value) or value is None:
        return []
    
    # If it's a string, try to parse it
    if isinstance(value, str):
        try:
            # Try parsing as JSON (handles ["field1", "field2"])
            return json.loads(value.replace("'", '"'))
        except:
            # If JSON parsing fails and it's not empty, treat as single field
            return [value] if value.strip() else []
    
    # If it's already a list, return it
    return value if isinstance(value, list) else []

def parse_entity_selectors(value):
    """
    Parse entitySelectors from CSV (likely stringified list of dicts)
    
    Args:
        value: Value from CSV (could be string, list, or NaN)
    
    Returns:
        List of entity selector dicts, or empty list
    """
   
    
    # Return empty list for None/NaN
    if pd.isna(value) or value is None:
        return []
    
    # If it's a string, try to parse it as JSON
    if isinstance(value, str):
        try:
            # Replace single quotes with double quotes for valid JSON
            return json.loads(value.replace("'", '"'))
        except:
            # If parsing fails, return empty list
            return []
    
    # If it's already a list, return it
    return value if isinstance(value, list) else []

def parse_tags(value):
    """
    Parse tags from CSV (handles stringified lists)
    
    Args:
        value: Value from CSV (could be string, list, or NaN)
    
    Returns:
        List of tag strings, or empty list
    """
  
    
    # Return empty list for None/NaN
    if pd.isna(value) or value is None:
        return []
    
    # If it's a string, try to parse it
    if isinstance(value, str):
        try:
            # Try parsing as JSON (handles ["tag1", "tag2"])
            return json.loads(value.replace("'", '"'))
        except:
            # If JSON parsing fails, try splitting by comma
            return [t.strip() for t in value.split(',') if t.strip()]
    
    # If it's already a list, return it
    return value if isinstance(value, list) else []

def parse_tags(value):
    """
    Parse tags from CSV (handles stringified lists)
    
    Args:
        value: Value from CSV (could be string, list, or NaN)
    
    Returns:
        List of tag strings, or empty list
    """

    
    # Return empty list for None/NaN
    if pd.isna(value) or value is None:
        return []
    
    # If it's a string, try to parse it
    if isinstance(value, str):
        try:
            # Try parsing as JSON (handles ["tag1", "tag2"])
            return json.loads(value.replace("'", '"'))
        except:
            # If JSON parsing fails, try splitting by comma
            return [t.strip() for t in value.split(',') if t.strip()]
    
    # If it's already a list, return it
    return value if isinstance(value, list) else []

def parse_score_mapping(value):
    """
    Parse scoreMapping from CSV (handles stringified dict)
    
    Args:
        value: Value from CSV (could be string, dict, or NaN)
    
    Returns:
        Dict with scoreMapping structure, or None
    """
    import json
    import pandas as pd
    
    # Return None for None/NaN
    if pd.isna(value) or value is None:
        return None
    
    # If it's a string, try to parse it as JSON
    if isinstance(value, str):
        try:
            # Replace single quotes with double quotes for valid JSON
            return json.loads(value.replace("'", '"'))
        except:
            # If parsing fails, return None
            return None
    
    # If it's already a dict, return it
    return value if isinstance(value, dict) else None

def parse_list_field(value):
    """
    Parse generic list field from CSV (handles stringified lists)
    
    Args:
        value: Value from CSV (could be string, list, or NaN)
    
    Returns:
        List of values, or empty list
    """
 
    
    # Return empty list for None/NaN
    if pd.isna(value) or value is None:
        return []
    
    # If it's a string, try to parse it as JSON
    if isinstance(value, str):
        try:
            # Replace single quotes with double quotes for valid JSON
            return json.loads(value.replace("'", '"'))
        except:
            # If parsing fails, return empty list
            return []
    
    # If it's already a list, return it
    return value if isinstance(value, list) else []