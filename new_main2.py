from sumo_cse_functions import fetch_all_rules, fetch_rule_types

#from csv_functions import clean_and_export_to_csv, normalize_rule_types_in_csv, import_csv, parse_entity_selectors
#from preprocess_cse_rules import extract_rule_tags
from sumo_lap_functions import fetch_saved_searches #, clean_and_export_searches
from json_processing import export_cse_rules_json,  duplicate_rules_from_csv,export_cse_rules_json
from csv_processing import export_cse_rules, export_saved_searches, export_rules_for_tagging, import_and_update_tags
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

def show_dynamic_menu(functions_dict):
    """
    Build menu dynamically from functions dictionary
    
    Args:
        functions_dict: Dict of {option_name: function}
    """
    console.print("\n[bold cyan]===== Sumo Logic CSE Tool =====[/bold cyan]")
    
    # Automatically number the options
    for idx, option_name in enumerate(functions_dict.keys(), 1):
        console.print(f"{idx}. {option_name}")
    
    console.print(f"{len(functions_dict) + 1}. Exit")
    console.print("[bold cyan]===============================[/bold cyan]\n")
    
    choice = input(f"Select an option (1-{len(functions_dict) + 1}): ").strip()
    return choice


def main():
    """Main program with dynamic menu"""
    
    # Get org credentials
    org = "ORG1"
    access_id = os.getenv(f"{org}_ACCESS_ID")
    access_key = os.getenv(f"{org}_ACCESS_KEY")
    endpoint = os.getenv(f"{org}_ENDPOINT")
    
    if not all([access_id, access_key, endpoint]):
        console.log(f"Missing credentials for {org}", style="bold red")
        return
    
    console.log(f"Connected to {org}", style="bold green")
    
    # Define menu options - just add/remove functions here!
    menu_options = {
        "Export CSE Rules (JSON)": lambda: export_cse_rules_json(org, access_id, access_key, endpoint),
        "Export CSE Rules (CSV - Full)": lambda: export_cse_rules(org, access_id, access_key, endpoint),
        "Export Rules for Tagging (CSV - Simple)": lambda: export_rules_for_tagging(org, access_id, access_key, endpoint),
        #"Import and Create Rules (JSON)": lambda: import_and_create_rules_json(access_id, access_key, endpoint),
        "Duplicate Rules from CSV": lambda: duplicate_rules_from_csv(access_id, access_key, endpoint),
        "Import and Update Tags (CSV)": lambda: import_and_update_tags(access_id, access_key, endpoint),
        "Export Saved Searches": lambda: export_saved_searches(org, access_id, access_key, endpoint),
        #"Get Rule Type Inventory": lambda: fetch_rule_types(access_id, access_key, endpoint),
    }
    
    while True:
        choice = show_dynamic_menu(menu_options)
        
        try:
            choice_num = int(choice)
            
            if choice_num == len(menu_options) + 1:
                console.log("Goodbye!", style="bold cyan")
                break
            
            if 1 <= choice_num <= len(menu_options):
                # Get the function by index
                func = list(menu_options.values())[choice_num - 1]
                func()  # Execute it
            else:
                console.log("Invalid choice", style="yellow")
                
        except ValueError:
            console.log("Please enter a number", style="yellow")
        except Exception as e:
            console.log(f"Error: {str(e)}", style="bold red")


if __name__ == "__main__":
    main()