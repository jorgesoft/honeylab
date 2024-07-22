import json
import sys
from collections import defaultdict
from datetime import datetime

def analyze_alerts(file_path, output_path):
    counts = {
        'rule_level': defaultdict(int),
        'agent_name': defaultdict(int),
        'rule_description': defaultdict(int),
        'geo_location': defaultdict(int)
    }

    with open(file_path, 'r') as file:
        try:
            alerts = json.load(file)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return

    for alert in alerts:
        if not alert or not isinstance(alert, dict):
            continue

        source = alert.get('_source', {})

        # Count rule levels
        rule_level = source.get('rule', {}).get('level')
        if rule_level is not None:
            counts['rule_level'][rule_level] += 1

        # Count agent names
        agent_name = source.get('agent', {}).get('name')
        if agent_name:
            counts['agent_name'][agent_name] += 1

        # Count rule descriptions
        rule_description = source.get('rule', {}).get('description')
        if rule_description:
            counts['rule_description'][rule_description] += 1

        # Count geo locations (country names)
        geo_location = source.get('GeoLocation', {}).get('country_name')
        if geo_location:
            counts['geo_location'][geo_location] += 1

    # Convert defaultdict to dict for JSON serialization
    summary = {
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'rule_level': dict(counts['rule_level']),
        'agent_name': dict(counts['agent_name']),
        'rule_description': dict(counts['rule_description']),
        'geo_location': dict(counts['geo_location'])
    }

    # Save summary to output JSON file
    with open(output_path, 'w') as outfile:
        json.dump(summary, outfile, indent=4)

    print(f"Summary saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python analyze_alerts.py <path_to_alerts.json> <path_to_summary.json>")
        sys.exit(1)

    file_path = sys.argv[1]
    output_path = sys.argv[2]
    analyze_alerts(file_path, output_path)