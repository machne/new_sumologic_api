import os
import requests
import pandas as pd
import json
from dotenv import load_dotenv, find_dotenv
from rich.console import Console

console = Console()
load_dotenv(find_dotenv())


def delete_rules_from_csv():
    """
    Delete rules listed in CSV
    Requires: CSV with 'id' column containing rule IDs
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
    
    # Get CSV with rule IDs
    console.print("\n[bold cyan]CSV must have 'id' column with rule IDs (e.g., MATCH-S00123)[/bold cyan]")
    csv_filename = input("Enter CSV filename: ").strip().strip('"').strip("'")
    
    try:
        df = pd.read_csv(csv_filename)
        
        if 'id' not in df.columns:
            console.log("✗ CSV must have 'id' column", style="bold red")
            console.log(f"  Available columns: {df.columns.tolist()}")
            return []
        
        rule_ids = df['id'].dropna().tolist()
        console.log(f"✓ Found {len(rule_ids)} rule IDs to delete", style="bold green")
        
    except Exception as e:
        console.log(f"✗ Error reading CSV: {str(e)}", style="bold red")
        return []
    
    # Confirm deletion
    console.print(f"\n[bold red]⚠ WARNING: You are about to delete {len(rule_ids)} rules![/bold red]")
    console.print("This action cannot be undone!\n")
    
    for i, rule_id in enumerate(rule_ids[:5], 1):
        console.print(f"  {i}. {rule_id}")
    
    if len(rule_ids) > 5:
        console.print(f"  ... and {len(rule_ids) - 5} more")
    
    confirm = input("\nType 'DELETE' to confirm: ").strip()
    
    if confirm != 'DELETE':
        console.log("Cancelled", style="yellow")
        return []
    
    # Setup API
    auth = (access_id, access_key)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    
    results = []
    errors = []
    
    for rule_id in rule_ids:
        
        delete_url = f"{endpoint}/sec/v1/rules/{rule_id}"
        
        console.log(f"Deleting: {rule_id}")
        
        try:
            response = requests.delete(delete_url, auth=auth, headers=headers)
            response.raise_for_status()
            
            console.log(f"  ✓ Deleted", style="bold green")
            results.append(rule_id)
            
        except requests.exceptions.HTTPError as e:
            console.log(f"  ✗ HTTP Error: {e.response.status_code}", style="bold red")
            console.log(f"  Response: {e.response.text[:200]}")
            errors.append(rule_id)
        except Exception as e:
            console.log(f"  ✗ Error: {str(e)}", style="bold red")
            errors.append(rule_id)
    
    # Summary
    console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
    console.print(f"[bold green]✓ Deleted: {len(results)} rules[/bold green]")
    
    if errors:
        console.print(f"[bold red]✗ Failed: {len(errors)} rules[/bold red]")
        for rule_id in errors:
            console.log(f"  - {rule_id}", style="red")
    
    return results


if __name__ == "__main__":
    console.print("[bold red]Rule Deletion Tool[/bold red]\n")
    results = delete_rules_from_csv()