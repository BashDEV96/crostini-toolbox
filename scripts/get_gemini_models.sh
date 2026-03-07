#!/bin/bash

# Define your API key directly here (Keep this file private!)
source .env

# Define the output text file
OUTPUT_FILE="gemini_models_detailed.txt"

echo "Fetching detailed Gemini model info from Google AI Studio..."

# Ping the REST API and pipe the JSON directly into Python for formatting
curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=$GEMINI_API_KEY" | python3 -c "
import sys, json

try:
    data = json.load(sys.stdin)
    
    # Expanded header row for wider screens
    print(f'{\"MODEL NAME\":<40} | {\"INPUT\":<10} | {\"OUTPUT\":<10} | {\"API METHODS\":<35} | {\"DESCRIPTION\"}')
    print('-'*155)
    
    for m in data.get('models', []):
        name = m.get('name', 'N/A')
        desc = m.get('description', 'N/A').replace('\n', ' ')[:50] + '...' 
        inp = str(m.get('inputTokenLimit', 'N/A'))
        out = str(m.get('outputTokenLimit', 'N/A'))
        
        # Join the array of methods into a single readable string
        methods_list = m.get('supportedGenerationMethods', [])
        methods = ', '.join(methods_list)[:35]
        
        print(f'{name:<40} | {inp:<10} | {out:<10} | {methods:<35} | {desc}')
except Exception as e:
    print('Error parsing the API response. Double check your API key.')
" > "$OUTPUT_FILE"

echo "Success. Expanded model list exported to $OUTPUT_FILE"