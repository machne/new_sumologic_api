from urllib import response

import requests
import json

# Sumo Logic API Configuration
SUMO_ACCESS_ID = "suElwH1hUc2sfP"
SUMO_ACCESS_KEY = "tJP0UZDFtPoXuHI2Pb8rolHkZMPVjXSrNte77zi2HO09q8SHxHQaEQxiY3c47JR1"
SUMO_DEPLOYMENT = "fed"  # Change to your deployment (us1, us2, eu, au, etc.)

# Construct the API endpoint
#API_ENDPOINT = f"https://api.{SUMO_DEPLOYMENT}.sumologic.com/api/v1/content/folders/global/search"
API_ENDPOINT = "https://api.fed.sumologic.com/api/v1/logSearches"
def get_saved_searches():
    """
    Retrieve all saved searches from Sumo Logic
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
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text[:500]}")

        print(f"Status: {response.status_code}")
        print("\nFull Response:")
        print(json.dumps(response.json(), indent=2))


        # Check if request was successful
        response.raise_for_status()
        
        # Parse the response
        data = response.json()
        
        # Filter for saved searches (itemType = "Search")
        saved_searches = [
            item for item in data.get('children', []) 
            if item.get('itemType') == 'Search'
        ]
        
        print(f"Found {len(saved_searches)} saved searches:\n")
        
        for search in saved_searches:
            print(f"Name: {search.get('name')}")
            print(f"ID: {search.get('id')}")
            print(f"Created: {search.get('createdAt')}")
            print(f"Modified: {search.get('modifiedAt')}")
            print("-" * 50)
        
        return saved_searches
        
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        print(f"Response: {response.text}")
    except Exception as err:
        print(f"An error occurred: {err}")

if __name__ == "__main__":
    get_saved_searches()