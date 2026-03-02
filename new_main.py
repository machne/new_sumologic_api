from sumo_cse_functions import fetch_all_rules, fetch_rule_types

#from csv_functions import clean_and_export_to_csv, normalize_rule_types_in_csv, import_csv, parse_entity_selectors
#from preprocess_cse_rules import extract_rule_tags
from sumo_lap_functions import fetch_saved_searches #, clean_and_export_searches
from sumo_cse_sdk_functions import download_rules_inventory
from json_processing import export_cse_rules_json, import_and_create_rules_json
import os
import numpy as np  # 
import pandas as pd
from rich.console import Console
import requests
from dotenv import load_dotenv, find_dotenv
console = Console()
console.log('Loading Environment Variables...')

# Load environment variables
load_dotenv(find_dotenv())


def show_menu():
    """Display main menu and get user choice"""
    console.print("\n[bold cyan]===== Sumo Logic CSE Tool =====[/bold cyan]")
    console.print("1. Export CSE Rules to JSON")
    console.print("2. Export Saved Searches to CSV")
    console.print("3. Import and Create Rules from JSON")
    console.print("4. Get Rule Type Inventory")
    console.print("5. Exit")
    console.print("[bold cyan]===============================[/bold cyan]\n")
    
    choice = input("Select an option (1-5): ").strip()
    return choice
   
    
def export_saved_searches(org_name, access_id, access_key, endpoint):
    print(f"Exporting saved searches for {endpoint}...")
    searches = fetch_saved_searches(org_name, access_id, access_key, endpoint)

    console.log(f"DEBUG: Type of searches: {type(searches)}")
    console.log(f"DEBUG: Number of searches: {len(searches) if searches else 0}")

    if searches:
        df_searches, file_searches = clean_and_export_to_csv(searches, 'saved_searches', org_name)
    else:
        console.log("No searches found to export", style="yellow")


  
def get_rule_types(access_id, access_key, endpoint):
    
    api_url=endpoint+ "/sec/v1/rules"
    rule_types = fetch_rule_types(access_id, access_key, api_url)
    rule_types_list=(rule_types.keys())
    console.log(f"Rule Types and Counts: {rule_types}")
    console.log(f"Unique Rule Types: {rule_types_list}")

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


"""Main program loop"""
def main():

# Get org credentials
    ORGS = ["ORG1"]
    for org in ORGS:
        access_id=os.getenv(f"{org}_ACCESS_ID")
        access_key=os.getenv(f"{org}_ACCESS_KEY")
        endpoint=os.getenv(f"{org}_ENDPOINT")
        org_name=os.getenv(f"{org}_NAME")
        print(f"\nProcessing {org_name}...")
        print(f"\nProcessing {endpoint}...")

    
        if not all([access_id, access_key, endpoint, org_name]):
            console.log(f"Missing credentials for {org}", style="bold red")
        continue
    
    console.log(f"Connected to {org}", style="bold green")
    
    while True:
        choice = show_menu()
        
        try:
            if choice == "1":
                export_cse_rules_json(org_name, access_id, access_key, endpoint)
            
            elif choice == "2":
                export_saved_searches(org_name, access_id, access_key, endpoint)
            
            elif choice == "3":
                import_and_create_rules_json(access_id, access_key, endpoint)
            
            elif choice == "4":
                get_rule_types(access_id, access_key, endpoint)
            
            elif choice == "5":
                console.log("Goodbye!", style="bold cyan")
                break
            
            else:
                console.log("Invalid choice. Please select 1-5.", style="yellow")
        
        except Exception as e:
            console.log(f"Error: {str(e)}", style="bold red")
            console.log("Returning to menu...")

if __name__ == "__main__":
    main()