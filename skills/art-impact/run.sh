#!/usr/bin/env bash
# art-impact - find impactful art piece and summarize

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: art-impact \"Artwork Title\""
  exit 1
fi

QUERY="$1"

# URL‑encode the query using Python
ENCODED=$(python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1]))" "$QUERY")

# Query Wikipedia API
RESPONSE=$(curl -s "https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&titles=${ENCODED}&format=json")

# Parse JSON with Python to get page title and extract
PAGE_TITLE=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(list(data['query']['pages'].values())[0]['title'])")
PAGE_EXTRACT=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(list(data['query']['pages'].values())[0]['extract'])")

if [[ -z "$PAGE_TITLE" || -z "$PAGE_EXTRACT" ]]; then
  echo "Error: Could not find Wikipedia page for \"$QUERY\"."
  exit 1
fi

# Build the link
LINK="https://en.wikipedia.org/wiki/$PAGE_TITLE"

# Split the extract into two paragraphs (first 200 characters roughly)
PAR1=$(echo "$PAGE_EXTRACT" | head -c 200)
# Trim to nearest sentence boundary
PAR1=$(echo "$PAR1" | sed -E 's/([^.!?]+[.!?]+) */\1 /; s/ *$//')
PAR2=$(echo "$PAGE_EXTRACT" | tail -c +$((${#PAGE_EXTRACT}+1-200)) | sed -E 's/^[[:space:]]*//')

# Output
echo "Paragraph 1: $PAR1"
echo "Paragraph 2: $PAR2"
echo "Link: $LINK"