#!/bin/bash

# Check if the correct number of arguments are provided
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <username> <password>"
  exit 1
fi

# Parameters
USERNAME=$1
PASSWORD=$2
OUTPUT_FILE="alerts.json"
SIZE=1000  # Number of results per page
FROM=0

# Start with an empty output file
> $OUTPUT_FILE

# Fetch total count of alerts for the last 7 days
TOTAL=$(curl -s -u $USERNAME:$PASSWORD -k -X GET "https://127.0.0.1:9200/wazuh-alerts*/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "range": {
      "@timestamp": {
        "gte": "now-7d/d",
        "lte": "now/d"
      }
    }
  },
  "size": 0,
  "track_total_hits": true
}' | jq '.hits.total.value')

echo "Total alerts in the last 7 days: $TOTAL"

# Loop to fetch all alerts in batches of $SIZE
while [ $FROM -lt $TOTAL ]; do
  RESPONSE=$(curl -s -u $USERNAME:$PASSWORD -k -X GET "https://127.0.0.1:9200/wazuh-alerts*/_search?pretty" -H 'Content-Type: application/json' -d'
  {
    "_source": ["agent.name", "data.srcip", "rule.level", "rule.description", "@timestamp", "GeoLocation"],
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
    "size": '$SIZE',
    "from": '$FROM'
  }')

  # Append the current batch of results to the output file
  echo $RESPONSE | jq '.hits.hits' >> $OUTPUT_FILE

  FROM=$((FROM + SIZE))
done

echo "Results saved to $OUTPUT_FILE"
