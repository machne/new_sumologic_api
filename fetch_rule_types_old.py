from sumologic import SumoLogic

# Sumo Logic CSE API Configuration
SUMO_ACCESS_ID = "suElwH1hUc2sfP"
SUMO_ACCESS_KEY = "tJP0UZDFtPoXuHI2Pb8rolHkZMPVjXSrNte77zi2HO09q8SHxHQaEQxiY3c47JR1"
SUMO_DEPLOYMENT = "fed" 

# Step 1: Initialize the SDK client
sumo = SumoLogic(SUMO_ACCESS_ID, SUMO_ACCESS_KEY, endpoint='https://api.fed.sumologic.com/api')

# Step 2: Get all rules (no type filter)
print("Fetching all CSE rules...")
#rules = sumo.get_cse_rules(types=[])
rules = sumo.get_cse_rules()

# Step 3: Check how many rules we got
print(f"Total rules retrieved: {len(rules)}")

# Step 4: Look at what rule types exist
# Each rule is a dictionary, so we loop through and get the 'ruleType' field
print("\nExtracting rule types...")
rule_types = []
for rule in rules:
    rule_type = rule.get('ruleType')  # get() safely retrieves the value
    if rule_type:  # only add if it exists
        rule_types.append(rule_type)

# Step 5: Get unique types (remove duplicates)
unique_types = set(rule_types)  # set() removes duplicates

# Step 6: Print them nicely
print(f"\nUnique rule types found: {sorted(unique_types)}")

# Step 7: Count how many of each type
print("\nCount by type:")
for rule_type in sorted(unique_types):
    count = rule_types.count(rule_type)
    print(f"  {rule_type}: {count}")