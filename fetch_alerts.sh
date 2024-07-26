#!/bin/bash

# Check if the correct number of arguments are provided
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <username> <password>"
  exit 1
fi

# Parameters
USERNAME=$1
PASSWORD=$2
OUTPUT_FILE="/tmp/alerts.json"
SIZE=1000  # Number of results per page
FROM=0

# Start with an empty output file
> $OUTPUT_FILE

# Open JSON array
echo "[" > $OUTPUT_FILE

# Fetch total count of alerts for the last 7 days
TOTAL_RESPONSE=$(curl -s -u $USERNAME:$PASSWORD -k -X GET "https://127.0.0.1:9200/wazuh-alerts*/_search" -H 'Content-Type: application/json' -d'
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
}')

TOTAL=$(echo $TOTAL_RESPONSE | jq '.hits.total.value')

# Check if TOTAL is a valid number
if ! [[ $TOTAL =~ ^[0-9]+$ ]]; then
  echo "Error fetching total alerts: $TOTAL_RESPONSE"
  exit 1
fi

echo "Total alerts in the last 7 days: $TOTAL"

# Loop to fetch all alerts in batches of $SIZE
FIRST=true
while [ $FROM -lt $TOTAL ]; do
  RESPONSE=$(curl -s -u $USERNAME:$PASSWORD -k -X GET "https://127.0.0.1:9200/wazuh-alerts*/_search?pretty" -H 'Content-Type: application/json' -d'
  {
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
    "size": '$SIZE',
    "from": '$FROM'
  }')

  # Process the current batch of results
  HITS=$(echo $RESPONSE | jq '.hits.hits')

  if $FIRST; then
    FIRST=false
  else
    echo "," >> $OUTPUT_FILE
  fi

  # Append the current batch of results to the output file, removing the surrounding brackets
  echo $HITS | sed 's/^\[\(.*\)\]$/\1/' >> $OUTPUT_FILE

  FROM=$((FROM + SIZE))
done

# Close JSON array
echo "]" >> $OUTPUT_FILE

echo "Results saved to $OUTPUT_FILE"

# Save a copy of alerts.json with a timestamp
TIMESTAMP=$(date +%s)
mkdir -p /root/alerts
cp $OUTPUT_FILE /root/alerts/alerts${TIMESTAMP}.json

# Print out the final JSON for debugging
cat $OUTPUT_FILE