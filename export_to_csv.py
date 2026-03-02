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