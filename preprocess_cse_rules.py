import requests
import json
from datetime import datetime
from rich.console import Console

console = Console()
console.log('Loading Environment Variables...')


def extract_rule_tags(rules):
 
    print("Starting the tag extraction process...")
    processed_rules = []
    
    for rule in rules:
        # Create a copy to avoid modifying original
        rule_copy = rule.copy()
        
        # Get tags 
        tags = rule.get('tags', [])
        #print(f"DEBUG: Rule {rule.get('id')} has {len(tags)} tags: {tags}")

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
        #print(f"DEBUG: Extracted tags for rule {rule.get('id')}: {tag_dict}")

        # Add tag columns to rule
        rule_copy.update(tag_dict)
        processed_rules.append(rule_copy)

    #processed_rules = dict(sorted(processed_rules.items()))

    console.log(f"Extracted tags into separate columns")
    
    return processed_rules
