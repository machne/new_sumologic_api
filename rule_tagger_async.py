import os
import asyncio
import aiohttp
import pandas as pd
import json
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from rich.console import Console
from sumo_rule_payload_builder import (
    build_rule_create_update_payload, 
    build_rule_override_payload,
    get_rule_endpoint,
    is_sumo_native_rule
)

console = Console()
load_dotenv(find_dotenv())


async def update_single_rule(session, rule_data, auth, endpoint, delay=0.5, max_retries=3):
    """
    Update a single rule asynchronously with delay and retry logic
    
    Args:
        session: aiohttp ClientSession
        rule_data: Dict with all rule info
        auth: Tuple of (access_id, access_key)
        endpoint: Base API endpoint
        delay: Seconds to wait before making request
        max_retries: Number of times to retry on 500 errors
    
    Returns:
        Dict with result info
    """
    # Add delay BEFORE making request (throttling)
    await asyncio.sleep(delay)
    
    rule_name = rule_data['name']
    rule_id = rule_data['id']
    operation = rule_data['operation']
    payload = rule_data['payload']
    update_url = rule_data['url']
    tag_info = rule_data['tag_info']
    
    console.log(f"{operation}: {rule_name} ({rule_id})")
    console.log(f"  Tags: {tag_info}")
    console.log(f"  isPrototype: {payload['fields']['isPrototype']}")
    
    # Retry loop
    for attempt in range(max_retries):
        try:
            # Create BasicAuth
            auth_obj = aiohttp.BasicAuth(auth[0], auth[1])
            
            async with session.put(
                update_url,
                auth=auth_obj,
                json=payload,
                headers={"Content-Type": "application/json", "Accept": "application/json"}
            ) as response:
                
                if response.status == 200:
                    console.log(f"  ✓ {operation} successful", style="bold green")
                    return {
                        'success': True,
                        'name': rule_name,
                        'operation': operation
                    }
                elif response.status == 500:
                    # Server error - retry
                    error_text = await response.text()
                    
                    # Save failed payload for debugging
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    debug_file = f"failed_payload_{rule_id}_{timestamp}.json"
                    with open(debug_file, 'w') as f:
                        json.dump({
                            'rule_name': rule_name,
                            'rule_id': rule_id,
                            'operation': operation,
                            'url': update_url,
                            'payload': payload,
                            'response': error_text
                        }, f, indent=2)
                    console.log(f"  💾 Saved failed payload to: {debug_file}", style="dim")
                    
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2  # 2s, 4s, 6s
                        console.log(f"  ⚠ HTTP 500 - Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...", style="yellow")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        console.log(f"  ✗ HTTP Error: 500 (after {max_retries} retries)", style="bold red")
                        console.log(f"  Response: {error_text[:300]}")
                        return {
                            'success': False,
                            'name': rule_name,
                            'error': f"HTTP 500 after {max_retries} retries",
                            'debug_file': debug_file
                        }
                elif response.status == 400:
                    # Bad request - save payload and don't retry
                    error_text = await response.text()
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    debug_file = f"bad_request_{rule_id}_{timestamp}.json"
                    with open(debug_file, 'w') as f:
                        json.dump({
                            'rule_name': rule_name,
                            'rule_id': rule_id,
                            'operation': operation,
                            'url': update_url,
                            'payload': payload,
                            'response': error_text
                        }, f, indent=2)
                    
                    console.log(f"  ✗ HTTP Error: 400", style="bold red")
                    console.log(f"  Response: {error_text[:300]}")
                    console.log(f"  💾 Saved payload to: {debug_file}", style="dim")
                    return {
                        'success': False,
                        'name': rule_name,
                        'error': f"HTTP 400",
                        'debug_file': debug_file
                    }
                else:
                    # Other error - don't retry
                    error_text = await response.text()
                    console.log(f"  ✗ HTTP Error: {response.status}", style="bold red")
                    console.log(f"  Response: {error_text[:300]}")
                    return {
                        'success': False,
                        'name': rule_name,
                        'error': f"HTTP {response.status}"
                    }
                    
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                console.log(f"  ⚠ Error: {str(e)} - Retrying in {wait_time}s...", style="yellow")
                await asyncio.sleep(wait_time)
                continue
            else:
                console.log(f"  ✗ Error: {str(e)} (after {max_retries} retries)", style="bold red")
                return {
                    'success': False,
                    'name': rule_name,
                    'error': str(e)
                }
    
    # Should not reach here, but just in case
    return {
        'success': False,
        'name': rule_name,
        'error': 'Max retries exceeded'
    }


async def process_rules_batch(rules_to_process, auth, endpoint, batch_size=5):
    """
    Process multiple rules concurrently in batches
    
    Args:
        rules_to_process: List of rule data dicts
        auth: Authentication tuple
        endpoint: Base endpoint
        batch_size: Number of concurrent requests (default 5, safer for APIs)
    
    Returns:
        List of results
    """
    
    all_results = []
    
    # Create aiohttp session with connection limits
    connector = aiohttp.TCPConnector(limit=batch_size)
    timeout = aiohttp.ClientTimeout(total=120)  # Increased timeout
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        
        # Process in batches to avoid overwhelming the API
        for i in range(0, len(rules_to_process), batch_size):
            batch = rules_to_process[i:i + batch_size]
            
            console.print(f"\n[bold cyan]Processing batch {i//batch_size + 1} ({len(batch)} rules)...[/bold cyan]\n")
            
            # Stagger requests in the batch (0s, 0.5s, 1s, 1.5s, etc.)
            tasks = []
            for idx, rule in enumerate(batch):
                delay = idx * 0.5  # Stagger by 0.5 seconds each
                tasks.append(update_single_rule(session, rule, auth, endpoint, delay=delay))
            
            # Run batch concurrently
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle any exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    console.log(f"  ✗ Unexpected error: {str(result)}", style="bold red")
                    all_results.append({'success': False, 'error': str(result)})
                else:
                    all_results.append(result)
            
            # Delay between batches
            if i + batch_size < len(rules_to_process):
                console.print(f"[dim]Waiting 2 seconds before next batch...[/dim]")
                await asyncio.sleep(2)
    
    return all_results


def manage_rule_tags_async():
    """
    Update tags and isPrototype for rules using async processing
    Much faster for bulk updates!
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
    
    # Get CSV with changes
    console.print("\n[bold cyan]Step 1: CSV with changes[/bold cyan]")
    console.print("Required columns: name, tags (comma-separated), isPrototype")
    csv_filename = input("Enter CSV filename: ").strip().strip('"').strip("'")
    
    try:
        df = pd.read_csv(csv_filename)
        
        required_cols = ['name', 'tags', 'isPrototype']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            console.log(f"✗ CSV missing columns: {missing_cols}", style="bold red")
            console.log(f"  Available columns: {df.columns.tolist()}")
            return []
        
        console.log(f"✓ Loaded {len(df)} rules from CSV", style="bold green")
        
    except Exception as e:
        console.log(f"✗ Error reading CSV: {str(e)}", style="bold red")
        return []
    
    # Get JSON inventory
    console.print("\n[bold cyan]Step 2: JSON inventory[/bold cyan]")
    json_filename = input("Enter JSON filename: ").strip().strip('"').strip("'")
    
    try:
        with open(json_filename, 'r', encoding='utf-8') as f:
            all_rules = json.load(f)
        
        console.log(f"✓ Loaded {len(all_rules)} rules from JSON", style="bold green")
        
        # Build lookup dict by name
        rules_by_name = {rule.get('name'): rule for rule in all_rules}
        
    except Exception as e:
        console.log(f"✗ Error reading JSON: {str(e)}", style="bold red")
        return []
    
    # Get batch size
    console.print("\n[bold cyan]Step 3: Concurrency settings[/bold cyan]")
    batch_size_input = input("Concurrent requests (default 3, max 10): ").strip()
    try:
        batch_size = int(batch_size_input) if batch_size_input else 3
        batch_size = min(batch_size, 10)  # Cap at 10
    except:
        batch_size = 3
    
    console.log(f"Using batch size: {batch_size}")
    console.log(f"[dim]Failed payloads will be saved to failed_payload_*.json files[/dim]")
    
    # Prepare all rules for processing
    rules_to_process = []
    not_found = []
    overrides_count = 0
    updates_count = 0
    
    console.print(f"\n[bold cyan]Preparing rules...[/bold cyan]")
    
    for idx, row in df.iterrows():
        
        rule_name = row.get('name')
        
        if pd.isna(rule_name):
            continue
        
        # Find rule in inventory
        inventory_rule = rules_by_name.get(rule_name)
        
        if not inventory_rule:
            not_found.append(rule_name)
            continue
        
        # Get rule details
        rule_id = inventory_rule.get('id')
        rule_type = inventory_rule.get('ruleType')
        
        # Get endpoint
        rule_endpoint = get_rule_endpoint(rule_type)
        if not rule_endpoint:
            console.log(f"  ⚠ Unknown type {rule_type}: {rule_name}", style="yellow")
            continue
        
        # Parse new tags
        new_tags_str = row.get('tags', '')
        if pd.isna(new_tags_str) or new_tags_str == '':
            new_non_mitre_tags = []
        else:
            new_non_mitre_tags = [tag.strip() for tag in str(new_tags_str).split(',') if tag.strip()]
        
        # Get existing MITRE tags
        existing_tags = inventory_rule.get('tags', [])
        mitre_tags = [tag for tag in existing_tags if tag.startswith('_mitreAttack')]
        
        # Combine tags
        combined_tags = mitre_tags + new_non_mitre_tags
        
        # Get isPrototype
        is_prototype = bool(row.get('isPrototype', False))
        
        # Modify rule
        modified_rule = inventory_rule.copy()
        modified_rule['tags'] = combined_tags
        modified_rule['isPrototype'] = is_prototype
        
        # Determine operation type
        is_native = is_sumo_native_rule(rule_id)
        
        if is_native:
            update_url = f"{endpoint}/sec/v1/rules/{rule_endpoint}/{rule_id}/override"
            payload = build_rule_override_payload(modified_rule, rule_type)
            operation = "Override"
            overrides_count += 1
        else:
            update_url = f"{endpoint}/sec/v1/rules/{rule_endpoint}/{rule_id}"
            payload = build_rule_create_update_payload(modified_rule, rule_type, name_modifier="")
            operation = "Update"
            updates_count += 1
        
        if not payload:
            console.log(f"  ✗ Failed to build payload for {rule_name}", style="red")
            continue
        
        # Add to processing queue
        rules_to_process.append({
            'name': rule_name,
            'id': rule_id,
            'operation': operation,
            'payload': payload,
            'url': update_url,
            'tag_info': f"{len(combined_tags)} total ({len(mitre_tags)} MITRE + {len(new_non_mitre_tags)} custom)"
        })
    
    console.log(f"✓ Prepared {len(rules_to_process)} rules for processing")
    console.log(f"  • Overrides: {overrides_count}")
    console.log(f"  • Updates: {updates_count}")
    
    if not rules_to_process:
        console.log("No rules to process!", style="yellow")
        return []
    
    # Process all rules asynchronously
    console.print(f"\n[bold cyan]Starting async processing...[/bold cyan]")
    
    auth = (access_id, access_key)
    
    # Run the async batch processor
    results = asyncio.run(process_rules_batch(rules_to_process, auth, endpoint, batch_size))
    
    # Calculate stats
    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]
    
    # Summary
    console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
    console.print(f"[bold green]✓ Processed {len(successful)}/{len(rules_to_process)} rules successfully[/bold green]")
    
    if failed:
        console.print(f"\n[bold red]✗ Failed: {len(failed)} rules[/bold red]")
        debug_files = []
        for fail in failed[:10]:
            error_msg = f"  - {fail.get('name', 'unknown')}: {fail.get('error', 'unknown error')}"
            console.log(error_msg, style="red")
            if 'debug_file' in fail:
                debug_files.append(fail['debug_file'])
        if len(failed) > 10:
            console.print(f"  ... and {len(failed) - 10} more")
        
        if debug_files:
            console.print(f"\n[dim]Debug files created: {len(debug_files)}[/dim]")
            for df in debug_files[:5]:
                console.print(f"  {df}", style="dim")
    
    if not_found:
        console.print(f"\n[yellow]⚠ Not found: {len(not_found)} rules[/yellow]")
        for name in not_found[:10]:
            console.log(f"  - {name}", style="yellow")
        if len(not_found) > 10:
            console.print(f"  ... and {len(not_found) - 10} more")
    
    return successful


if __name__ == "__main__":
    console.print("[bold cyan]Rule Tag & Prototype Manager (ASYNC)[/bold cyan]")
    console.print("Fast bulk updates with retry logic and debug logging\n")
    results = manage_rule_tags_async()