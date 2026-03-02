import requests
import os
import re
from sumologic import SumoLogic
from dotenv import load_dotenv, find_dotenv
import pandas as pd
from datetime import datetime
from rich.console import Console
from csv_functions import import_csv, clean_value, parse_entity_selectors, parse_tags, parse_score_mapping, parse_list_field,parse_group_by_fields

console = Console()
console.log('Loading Environment Variables...')

def fetch_rule_types(access_id, access_key, api_url):
    """
    Returns: dictionary with rule types and their counts
    """
    auth = (access_id, access_key)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    
    rule_types = {}
    offset = 0
    limit = 500
    
    while True:
        
       #print(f"DEBUG: Making request to {api_url} with offset={offset}, limit={limit}")
       #print(f"DEBUG: About to call {api_url}")
       #print(f"DEBUG: auth = {auth}")
       #print(f"DEBUG: params = {{'offset': {offset}, 'limit': {limit}}}")
       
        response = requests.get(
            api_url,
            auth=auth,
            headers=headers,
            params={"offset": offset, "limit": limit}
        )
        
        #print(f"DEBUG: Response status code: {response.status_code}")

        data = response.json()
        rules = data.get('data', {}).get('objects', [])
        
        for rule in rules:
            rule_type = rule.get('ruleType')
            console.log(f"Rule ID: {rule.get('id')}, Type: {rule_type}")
            if rule_type:
                rule_types[rule_type] = rule_types.get(rule_type, 0) + 1
                #print(f"{rule_type}, count: {rule_types[rule_type]}")

        
        print(f"{rule_type}, count: {rule_types[rule_type]}")
        if not data.get('data', {}).get('hasNextPage', False):
            break
        offset += limit
    
    return rule_types


def fetch_all_rules(access_id, access_key, api_url, max_rules):
    """Get all rules using direct API (bypasses SDK issues)"""
    auth = (access_id, access_key)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    
    all_rules = []
    offset = 0
    limit = 500
    expand = "tuningExpressions"
    
    while True:
        response = requests.get(
            api_url,
            auth=auth,
            headers=headers,
            params={"offset": offset, "limit": limit, "expand": expand}
        )
        
        console.log(f"Fetching rules with offset={offset}, limit={limit}...")
        data = response.json()
        rules = data.get('data', {}).get('objects', [])
        all_rules.extend(rules)
        console.log(f"Offset = {offset}, Fetched {len(rules)} rules (Total so far: {len(all_rules)})")
        
       # Check if we've hit max_rules
        if max_rules and len(all_rules) >= max_rules:
            all_rules = all_rules[:max_rules]  # Trim to exact count
            console.log(f"Reached max_rules limit: {max_rules}")
            break
        
        if not data.get('data', {}).get('hasNextPage', False):
            break
        
        offset += limit
    #print(f"DEBUG all_rule object type: {type(all_rules)}")
    #print(f"DEBUGall_rule object length: {len(all_rules)}")
    return all_rules

def extract_rule_tags(rules):
    """
    Extract custom tags from CSE rules and add as separate columns
    
    Args:
        rules: List of rule dictionaries
    
    Returns:
        List of rules with expanded tag columns
    """
    
    processed_rules = []
    
    for rule in rules:
        # Create a copy to avoid modifying original
        rule_copy = rule.copy()
        
        # Get tags 
        tags = rule.get('tags', [])
        
        # Parse tags and extract non-MITRE tags
        tag_dict = {}
        for tag in tags:
            # Skip MITRE Attack tags
            if tag.startswith('_mitreAttack'):
                continue
            
            # Parse tag format: "key:value"
            if ':' in tag:
                key, value = tag.split(':', 1)  # Split on first colon only
                tag_dict[f'tag_{key}'] = value
            else:
                # Tag without colon - store as-is
                tag_dict[f'tag_{tag}'] = 'TRUE'
        
        # Add tag columns to rule
        rule_copy.update(tag_dict)
        processed_rules.append(rule_copy)
    
    console.log(f"Extracted tags into separate columns")
    
    return processed_rules