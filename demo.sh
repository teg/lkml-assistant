#!/bin/bash  
# Trigger the fetch-patches Lambda to collect a small batch of patches
  aws lambda invoke \
    --function-name LkmlAssistant-FetchPatches-dev \
    --payload '{"page": 1, "per_page": 5, "process_all_pages": false, "fetch_discussions": true}' \
    response.json

  # Check the response
  cat response.json
