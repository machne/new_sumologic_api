from dotenv import load_dotenv, find_dotenv
import requests
from sumo_cse_functions import fetch_rule_types
import sys
load_dotenv(find_dotenv())


print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path}")