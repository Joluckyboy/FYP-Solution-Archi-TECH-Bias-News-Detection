#!/bin/bash

# Set environment variables
export DATABASE_URL="http://localhost:8011"

export SENTIMENT_URL="http://localhost:8012"
export EMOTION_URL="http://localhost:8013"
export PROPAGANDA_URL="http://localhost:8014"
export SCRAPER_URL="http://localhost:8015"
export FACTCHECK_URL="http://localhost:8016"

# export DATABASE_URL="http://service.chfwhitehats2024.games"

# export SENTIMENT_URL="http://api.chfwhitehats2024.games"
# export EMOTION_URL="http://api.chfwhitehats2024.games"
# export PROPAGANDA_URL="http://api.chfwhitehats2024.games"
# export SCRAPER_URL="http://api.chfwhitehats2024.games"
# export FACTCHECK_URL="http://api.chfwhitehats2024.games"

# Function to clean up background processes and unset environment variables
cleanup() {
    echo "Cleaning up..."
    kill $APP_PID
    unset SENTIMENT_URL
    unset EMOTION_URL
    unset PROPAGANDA_URL
    unset SCRAPER_URL
    unset DATABASE_URL
    unset FACTCHECK_URL
    exit 0
}

# Trap termination signals (e.g., SIGINT, SIGTERM) and call the cleanup function
trap cleanup SIGINT SIGTERM

# Start the app
uvicorn app:app --reload --port 8010 &
APP_PID=$!

# Wait for the app process to finish
wait $APP_PID