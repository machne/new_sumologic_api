# export_rules_tags
import os
import re
from sumologic import SumoLogic
from dotenv import load_dotenv, find_dotenv
import pandas as pd
from datetime import datetime
from rich.console import Console

# Initialize console for rich logging
console = Console()
console.log('Loading Environment Variables...')
load_dotenv(find_dotenv())

# List of customers to process

CUST = ["ORG1"]


# clean the results for excel
def clean_for_excel(value):
    """Quick function to clean illegal characters"""
    # Convert everything to string first to avoid array issues
    if value is None:
        return ''
   
    str_value = str(value)
   
    # Remove control characters that cause IllegalCharacterError
    illegal_chars = [chr(i) for i in range(32) if i not in [9, 10, 13]]
    for char in illegal_chars:
        str_value = str_value.replace(char, '')
   
    # Truncate if too long
    if len(str_value) > 32000:
        str_value = str_value[:32000] + "... [TRUNCATED]"
   
    return str_value


# Function to clean sheet names for Excel compatibility
def clean_sheet_name(name):
    # Replace illegal characters and ensure sheet name is not too long
    cleaned = re.sub(r'[\\/*?:\[\]]', '_', str(name))
    return cleaned[:31]  # Excel sheet names can't exceed 31 characters

# Function to clean dataframe values for Excel compatibility
def clean_dataframe_for_excel(df):
    # Create a copy to avoid modifying the original
    df_clean = df.copy()
   
    # Clean string columns
    for col in df_clean.columns:
        if df_clean[col].dtype == 'object':  # Only clean string columns
            df_clean[col] = df_clean[col].astype(str).apply(
                lambda x: re.sub(r'[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]', '', x)
            )
    return df_clean

# Function to extract specific tags and create new columns
def extract_tags_to_columns(df):
    # Make a copy of the dataframe
    df_with_tags = df.copy()
   
    # Create new columns for each tag type we want to extract
    tag_types = ['active', 'event_label', 'priority', 'event_type', 'deployed', 'product', 'platform', 'casemaker']
    for tag_type in tag_types:
        df_with_tags[tag_type] = None
   
    # Process each row
    for idx, row in df_with_tags.iterrows():
        if 'tags' in row and row['tags']:
            tags = row['tags']
            # Handle if tags is already a list or if it's a string representation of a list
            if isinstance(tags, str):
                # Try to convert string representation to list
                try:
                    tags = eval(tags)
                except:
                    tags = tags.strip('[]').split(',')
           
            # Extract values for each tag type
            for tag in tags:
                tag = tag.strip("' ")
                for tag_type in tag_types:
                    if tag.startswith(f"{tag_type}:"):
                        value = tag.split(':', 1)[1]
                        df_with_tags.at[idx, tag_type] = value
   
    return df_with_tags

# Process each customer
for c in CUST:
    try:
        console.log(f"Processing customer: {c}")
       
        # Initialize SumoLogic API client for this customer
        sumo = SumoLogic(
            accessId=os.getenv(f"{c}.ACCESS_ID"),
            accessKey=os.getenv(f"{c}.ACCESS_KEY"),
            endpoint=os.getenv(f"{c}.ENDPOINT")
        )
       
        # Create filename with customer name and current timestamp
        now = datetime.now()
        file_name = f"{c}-{now.strftime('%Y%m%d-%H%M')}.xlsx"
        console.log(f'File name: {file_name}')
        console.log(sumo.endpoint)
        # Define rule types and query
        console.log(f"Building Query for {c} ...")
        rule_types = ['match', 'aggregation', 'chain', 'threshold', 'first seen', 'outlier']
        query = ""  # No filtering criteria
       
        # Get rules from the API
        console.log(f"Retrieving Rules for {c}...")
        cse_rules = sumo.get_cse_rules(query_string=query, types=rule_types)
        if not cse_rules:
            console.log(f"No rules found for {c}")
            continue
        else: console.log('Got the rules!')    
        console.log('Building DataFrame...')
        df = pd.DataFrame(cse_rules)
        #console.log(f'Got {df.count} rules!')
        # Select only the columns we want to export
        columns_to_export = [
            'category',
            'contentType',
            'created',
            'createdBy',
            'enabled',
            'id',
            'isPrototype',
            'lastUpdated',
            'lastUpdatedBy',
            'name',
            'ruleType',
            'expression',
            'summaryExpression',
            'tuningExpressions',
            'descriptionExpression',
            'version',
            'tags'  # Keep tags for extraction
        ]
       
        # Filter the DataFrame to only include desired columns
        # Use a list comprehension to only include columns that exist in the DataFrame
        existing_columns = [col for col in columns_to_export if col in df.columns]
        df = df[existing_columns]
       
        # Clean the dataframe for Excel compatibility
        df_clean = clean_dataframe_for_excel(df)
       
        # Extract tags to separate columns
        df_clean = extract_tags_to_columns(df_clean)
       
        # Create a safe sheet name
        safe_sheet_name = clean_sheet_name(c)
       
        console.log('Exporting to Excel...')
        try:
            # Try to write to the existing file in append mode
            with pd.ExcelWriter(file_name, engine="openpyxl", mode="a", if_sheet_exists='replace') as writer:
                df_clean.to_excel(writer, sheet_name=safe_sheet_name, index=False)
        except FileNotFoundError:
            # If file doesn't exist, create it
            with pd.ExcelWriter(file_name, engine="openpyxl", mode="w") as writer:
                df_clean.to_excel(writer, sheet_name=safe_sheet_name, index=False)
       
        console.log(f"Successfully wrote data for {c} to: {file_name}")
       
    except Exception as e:
        console.log(f"Error processing {c}: {str(e)}", style="bold red")

console.log(f"Export complete.")