#!/bin/bash

# Source the .env file to load environment variables
source ./.env

# Check if the API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY environment variable is not set."
    exit 1
fi

# Make the API request and extract the model IDs
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY" | jq -r '.data[].id' > openai_models.txt

echo "List of OpenAI models saved to openai_models.txt"