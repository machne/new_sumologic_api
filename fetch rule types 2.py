from sumologic import SumoLogic

SUMO_ACCESS_ID = "suElwH1hUc2sfP"
SUMO_ACCESS_KEY = "tJP0UZDFtPoXuHI2Pb8rolHkZMPVjXSrNte77zi2HO09q8SHxHQaEQxiY3c47JR1"
SUMO_DEPLOYMENT = "fed" 

sumo = SumoLogic(SUMO_ACCESS_ID, SUMO_ACCESS_KEY, endpoint='https://api.fed.sumologic.com/api')

# Try adding more rule types
print("Fetching all CSE rules...")
#rules = sumo.get_cse_rules(types=["match", "aggregation", "chain", "threshold", "templated", "first seen", "outlier"])
rules = sumo.get_cse_rules(types='Any')  #types=[])

print(f"Total rules retrieved: {len(rules)}")

# Extract and count types
rule_types = []
for rule in rules:
    rule_type = rule.get('ruleType')
    if rule_type:
        rule_types.append(rule_type)

unique_types = set(rule_types)
print(f"\nUnique rule types found: {sorted(unique_types)}")

print("\nCount by type:")
for rule_type in sorted(unique_types):
    count = rule_types.count(rule_type)
    print(f"  {rule_type}: {count}")