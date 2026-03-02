"""
Sumo Logic CSE Rule Payload Builder
Builds proper API payloads for all rule types based on official Sumo templates
"""

"""
Sumo Logic CSE Rule Payload Builder
Builds proper API payloads for creating, updating, and overriding rules
"""

def build_rule_create_update_payload(rule_dict, rule_type, name_modifier=""):
    """
    Build payload for creating or updating CSE rules
    
    Args:
        rule_dict: Dictionary with rule data (from JSON export or modified)
        rule_type: Rule type string (match, threshold, chain, etc.)
        name_modifier: String to append to name (e.g., "_copy")
    
    Returns:
        Dict with proper {"fields": {...}} structure, or None if unsupported type
    """
    
    # Common fields for ALL rule types
    common_fields = {
        'assetField': rule_dict.get('assetField'),
        'category': rule_dict.get('category'),
        'enabled': rule_dict.get('enabled'),
        'entitySelectors': rule_dict.get('entitySelectors'),
        'isPrototype': rule_dict.get('isPrototype'),
        'name': f"{rule_dict.get('name')}{name_modifier}",
        'summaryExpression': rule_dict.get('summaryExpression'),
        'tags': rule_dict.get('tags'),
    }
    
    # Type-specific fields (same as before)
    if rule_type == 'match':
        specific_fields = {
            'description': rule_dict.get('description'),
            'expression': rule_dict.get('expression'),
            'score': rule_dict.get('score'),
            'stream': rule_dict.get('stream'),
        }
    
    elif rule_type == 'templated match':
        specific_fields = {
            'descriptionExpression': rule_dict.get('descriptionExpression'),
            'expression': rule_dict.get('expression'),
            'nameExpression': rule_dict.get('nameExpression'),
            'scoreMapping': rule_dict.get('scoreMapping'),
            'stream': rule_dict.get('stream'),
        }
    
    elif rule_type == 'threshold':
        specific_fields = {
            'countDistinct': rule_dict.get('countDistinct'),
            'countField': rule_dict.get('countField'),
            'description': rule_dict.get('description'),
            'expression': rule_dict.get('expression'),
            'groupByFields': rule_dict.get('groupByFields'),
            'limit': rule_dict.get('limit'),
            'score': rule_dict.get('score'),
            'stream': rule_dict.get('stream'),
            'version': rule_dict.get('version'),
            'windowSize': rule_dict.get('windowSizeName'),
            'windowSizeMilliseconds': str(rule_dict.get('windowSize')) if rule_dict.get('windowSize') else None,
        }
    
    elif rule_type == 'chain':
        expressions_and_limits = rule_dict.get('expressionsAndLimits', [])
        if expressions_and_limits:
            cleaned_expressions = []
            for expr in expressions_and_limits:
                cleaned_expressions.append({
                    'expression': expr.get('expression'),
                    'limit': expr.get('limit')
                })
            expressions_and_limits = cleaned_expressions
        
        specific_fields = {
            'description': rule_dict.get('description'),
            'expressionsAndLimits': expressions_and_limits,
            'groupByFields': rule_dict.get('groupByFields'),
            'ordered': rule_dict.get('ordered'),
            'score': rule_dict.get('score'),
            'stream': rule_dict.get('stream'),
            'windowSize': rule_dict.get('windowSizeName'),
            'windowSizeMilliseconds': str(rule_dict.get('windowSize')) if rule_dict.get('windowSize') else None,
        }
    
    elif rule_type == 'aggregation':
        specific_fields = {
            'aggregationFunctions': rule_dict.get('aggregationFunctions'),
            'descriptionExpression': rule_dict.get('descriptionExpression'),
            'groupByAsset': rule_dict.get('groupByAsset'),
            'groupByFields': rule_dict.get('groupByFields'),
            'matchExpression': rule_dict.get('matchExpression'),
            'nameExpression': rule_dict.get('nameExpression'),
            'scoreMapping': rule_dict.get('scoreMapping'),
            'stream': rule_dict.get('stream'),
            'triggerExpression': rule_dict.get('triggerExpression'),
            'windowSize': rule_dict.get('windowSizeName'),
            'windowSizeMilliseconds': str(rule_dict.get('windowSize')) if rule_dict.get('windowSize') else None,
        }
    
    elif rule_type == 'outlier':
        specific_fields = {
            'nameExpression': rule_dict.get('nameExpression'),
            'groupByFields': rule_dict.get('groupByFields'),
            'score': rule_dict.get('score'),
            'baselineWindowSize': rule_dict.get('baselineWindowSize'),
            'retentionWindowSize': rule_dict.get('retentionWindowSize'),
            'floorValue': rule_dict.get('floorValue'),
            'deviationThreshold': rule_dict.get('deviationThreshold'),
            'descriptionExpression': rule_dict.get('descriptionExpression'),
            'matchExpression': rule_dict.get('matchExpression'),
            'aggregationFunctions': rule_dict.get('aggregationFunctions'),
            'windowSize': rule_dict.get('windowSizeName'),
            'windowSizeMilliseconds': str(rule_dict.get('windowSize')) if rule_dict.get('windowSize') else None,
        }
    
    elif rule_type == 'first-seen':
        specific_fields = {
            'descriptionExpression': rule_dict.get('descriptionExpression'),
            'nameExpression': rule_dict.get('nameExpression'),
            'filterExpression': rule_dict.get('filterExpression'),
            'valueFields': rule_dict.get('valueFields'),
            'valueExpression': rule_dict.get('valueExpression'),
            'groupByFields': rule_dict.get('groupByFields'),
            'score': rule_dict.get('score'),
            'version': rule_dict.get('version'),
            'baselineWindowSize': rule_dict.get('baselineWindowSize'),
            'retentionWindowSize': rule_dict.get('retentionWindowSize'),
            'baselineType': rule_dict.get('baselineType'),
        }
    
    else:
        return None
    
    # Merge common + specific
    all_fields = {**common_fields, **specific_fields}
    
    # Optional common fields
    if rule_dict.get('parentJaskId'):
        all_fields['parentJaskId'] = rule_dict.get('parentJaskId')
    
    if rule_dict.get('suppressionWindowSize'):
        all_fields['suppressionWindowSize'] = rule_dict.get('suppressionWindowSize')
    
    if rule_dict.get('tuningExpressionIds'):
        all_fields['tuningExpressionIds'] = rule_dict.get('tuningExpressionIds')
    
    # Remove None values
    all_fields = {k: v for k, v in all_fields.items() if v is not None}
    
    return {"fields": all_fields}


def build_rule_override_payload(rule_dict, rule_type):
    """
    Build payload for overriding Sumo native rules (rules with "S" in ID)
    Endpoint: /rules/{type}/{id}/override
    
    Args:
        rule_dict: Dictionary with rule data
        rule_type: Rule type string
    
    Returns:
        Dict with proper {"fields": {...}} structure for override
    """
    
    # Common override fields (all types)
    common_override = {
        'tuningExpressionIds': rule_dict.get('tuningExpressionIds'),
        'isPrototype': rule_dict.get('isPrototype'),
        'entitySelectors': rule_dict.get('entitySelectors'),
        'name': rule_dict.get('name'),
        'ruleDescription': rule_dict.get('description') or rule_dict.get('descriptionExpression'),
        'summaryExpression': rule_dict.get('summaryExpression'),
        'suppressionWindowSize': rule_dict.get('suppressionWindowSize'),
        'tags': rule_dict.get('tags'),
    }
    
    # Type-specific override fields
    if rule_type == 'match':
        specific_override = {}
    
    elif rule_type == 'templated match':
        specific_override = {
            'descriptionExpression': rule_dict.get('descriptionExpression'),
            'nameExpression': rule_dict.get('nameExpression'),
            'scoreMapping': rule_dict.get('scoreMapping'),
        }
    
    elif rule_type == 'threshold':
        specific_override = {
            'description': rule_dict.get('description'),
            'groupByFields': rule_dict.get('groupByFields'),
            'limit': rule_dict.get('limit'),
            'score': rule_dict.get('score'),
            'windowSize': rule_dict.get('windowSizeName'),
            'windowSizeMilliseconds': str(rule_dict.get('windowSize')) if rule_dict.get('windowSize') else None,
        }
    
    elif rule_type == 'chain':
        # Note: chain override uses 'limits' not 'expressionsAndLimits'
        limits = rule_dict.get('expressionsAndLimits', [])
        if limits:
            cleaned_limits = []
            for idx, lim in enumerate(limits):
                cleaned_limits.append({
                    'limit': lim.get('limit'),
                    'index': idx
                })
            limits = cleaned_limits
        
        specific_override = {
            'description': rule_dict.get('description'),
            'groupByFields': rule_dict.get('groupByFields'),
            'score': rule_dict.get('score'),
            'windowSize': rule_dict.get('windowSizeName'),
            'windowSizeMilliseconds': str(rule_dict.get('windowSize')) if rule_dict.get('windowSize') else None,
            'limits': limits,
        }
    
    elif rule_type == 'aggregation':
        specific_override = {
            'descriptionExpression': rule_dict.get('descriptionExpression'),
            'groupByFields': rule_dict.get('groupByFields'),
            'nameExpression': rule_dict.get('nameExpression'),
            'scoreMapping': rule_dict.get('scoreMapping'),
            'windowSize': rule_dict.get('windowSizeName'),
            'windowSizeMilliseconds': str(rule_dict.get('windowSize')) if rule_dict.get('windowSize') else None,
        }
    
    elif rule_type == 'outlier':
        specific_override = {
            'nameExpression': rule_dict.get('nameExpression'),
            'floorValue': str(rule_dict.get('floorValue')) if rule_dict.get('floorValue') else None,
            'groupByFields': rule_dict.get('groupByFields'),
            'descriptionExpression': rule_dict.get('descriptionExpression'),
            'baselineWindowSize': rule_dict.get('baselineWindowSize'),
            'deviationThreshold': str(rule_dict.get('deviationThreshold')) if rule_dict.get('deviationThreshold') else None,
            'retentionWindowSize': rule_dict.get('retentionWindowSize'),
            'score': rule_dict.get('score'),
            'windowSize': rule_dict.get('windowSizeName'),
            'windowSizeMilliseconds': str(rule_dict.get('windowSize')) if rule_dict.get('windowSize') else None,
        }
    
    elif rule_type == 'first-seen':
        specific_override = {
            'baselineWindowSize': rule_dict.get('baselineWindowSize'),
            'descriptionExpression': rule_dict.get('descriptionExpression'),
            'groupByFields': rule_dict.get('groupByFields'),
            'nameExpression': rule_dict.get('nameExpression'),
            'retentionWindowSize': rule_dict.get('retentionWindowSize'),
            'score': rule_dict.get('score'),
        }
    
    else:
        return None
    
    # Merge
    all_fields = {**common_override, **specific_override}
    
    # Remove None values
    all_fields = {k: v for k, v in all_fields.items() if v is not None}
    
    return {"fields": all_fields}


def get_rule_endpoint(rule_type):
    """Get API endpoint path for a given rule type"""
    endpoint_map = {
        'match': 'match',
        'templated match': 'templated',
        'threshold': 'threshold',
        'chain': 'chain',
        'aggregation': 'aggregation',
        'first seen': 'first-seen',
        'outlier': 'outlier'
    }
    
    return endpoint_map.get(rule_type)


def is_sumo_native_rule(rule_id):
    """Check if rule is Sumo native (has 'S' in ID like MATCH-S00922)"""
    return '-S' in str(rule_id)