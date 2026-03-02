import requests
import json
import pandas as pd
from datetime import datetime

# Sumo Logic API Configuration
SUMO_ACCESS_ID = "suElwH1hUc2sfP"
SUMO_ACCESS_KEY = "tJP0UZDFtPoXuHI2Pb8rolHkZMPVjXSrNte77zi2HO09q8SHxHQaEQxiY3c47JR1"
SUMO_DEPLOYMENT = "fed"  # Change to your deployment (us1, us2, eu, au, etc.)

# Construct the API endpoint
#API_ENDPOINT = f"https://api.{SUMO_DEPLOYMENT}.sumologic.com/api/v1/content/folders/global"
API_ENDPOINT = "https://api.fed.sumologic.com/api/v1/logSearches"
def list_all_content():
    """
    Retrieve all content from Sumo Logic
    """
    
    # Set up authentication
    auth = (SUMO_ACCESS_ID, SUMO_ACCESS_KEY)
    
    # Set headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        # Make the API request
        response = requests.get(
            API_ENDPOINT,
            auth=auth,
            headers=headers
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        # Parse the response
        data = response.json()
        
        # Print the raw response to see what we got
        print("Raw API Response:")
        print(json.dumps(data, indent=2))
        return data
        
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as err:
        print(f"An error occurred: {err}")
def export_to_csv(data, filename=None):
    """
    Export JSON data to CSV file using pandas
    """
    if not data:
        print("No data to export")
        return
    
    # Generate filename with timestamp if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sumo_content_{timestamp}.csv"
    
    try:
        # Handle if data is a dict with 'children' key
        if isinstance(data, dict) and 'logSearches' in data:
            df = pd.json_normalize(data['logSearches'])
        elif isinstance(data, dict):
            df = pd.json_normalize([data])
        elif isinstance(data, list):
            df = pd.json_normalize(data)
        else:
            print("Unexpected data format")
            return
        
        # Export to CSV
        df.to_csv(filename, index=False)
        
        print(f"\nSuccessfully exported to {filename}")
        print(f"Total rows: {len(df)}")
        print(f"Total columns: {len(df.columns)}")
        print(f"\nColumn names:")
        print(df.columns.tolist())
        
        return df
        
    except Exception as e:
        print(f"Error exporting to CSV: {e}")
        return None
if __name__ == "__main__":
    # Get the data
    data = list_all_content()
    
    # Export to CSV
    if data:
        df = export_to_csv(data)