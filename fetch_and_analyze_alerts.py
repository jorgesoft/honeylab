import json
import sys
from collections import defaultdict
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth

def fetch_and_analyze_alerts(username, password, output_path):
    SIZE = 1000  # Number of results per page
    FROM = 0

    # Elasticsearch URL
    es_url = "https://127.0.0.1:9200/wazuh-alerts*/_search"

    # Query for total count of alerts for the last 7 days
    total_query = {
        "query": {
            "range": {
                "@timestamp": {
                    "gte": "now-7d/d",
                    "lte": "now/d"
                }
            }
        },
        "size": 0,
        "track_total_hits": True
    }

    # Fetch total count
    response = requests.get(es_url, auth=HTTPBasicAuth(username, password), headers={'Content-Type': 'application/json'}, json=total_query, verify=False)
    if response.status_code != 200:
        print(f"Error fetching total alerts: {response.text}")
        return

    total = response.json().get('hits', {}).get('total', {}).get('value', 0)
    print(f"Total alerts in the last 7 days: {total}")

    counts = {
        'rule_level': defaultdict(int),
        'agent_name': defaultdict(int),
        'rule_description': defaultdict(int),
        'geo_location': defaultdict(int)
    }

    # Loop to fetch all alerts in batches of SIZE
    while FROM < total:
        query = {
            "_source": ["agent.name", "rule.level", "rule.description", "@timestamp", "GeoLocation"],
            "query": {
                "bool": {
                    "filter": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": "now-7d/d",
                                    "lte": "now/d"
                                }
                            }
                        }
                    ]
                }
            },
            "sort": [
                {
                    "@timestamp": {
                        "order": "desc"
                    }
                }
            ],
            "size": SIZE,
            "from": FROM
        }

        response = requests.get(es_url, auth=HTTPBasicAuth(username, password), headers={'Content-Type': 'application/json'}, json=query, verify=False)
        if response.status_code != 200:
            print(f"Error fetching alerts: {response.text}")
            return

        hits = response.json().get('hits', {}).get('hits', [])
        for alert in hits:
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

        FROM += SIZE

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
    if len(sys.argv) != 4:
        print("Usage: python fetch_and_analyze_alerts.py <username> <password> <output_path>")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]
    output_path = sys.argv[3]
    fetch_and_analyze_alerts(username, password, output_path)
