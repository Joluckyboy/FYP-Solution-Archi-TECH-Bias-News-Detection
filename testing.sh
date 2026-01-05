#!/bin/bash

# Set environment variables
export DATABASE_URL="http://localhost:8011"
export SENTIMENT_URL="http://localhost:8012"
export EMOTION_URL="http://localhost:8013"
export PROPAGANDA_URL="http://localhost:8014"
export SCRAPER_URL="http://localhost:8015"
export FACTCHECK_URL="http://localhost:8016"

# Function to kill process using a specific port
kill_port() {
    PORT=$1
    PID=$(lsof -t -i:$PORT)
    if [ -n "$PID" ]; then
        echo "Killing process on port $PORT (PID: $PID)"
        kill -9 $PID
    fi
}

# Kill processes using the ports
kill_port 8011
kill_port 8012
kill_port 8013
kill_port 8014
kill_port 8015
kill_port 8016

# Function to clean up background processes and unset environment variables
cleanup() {
    echo "Cleaning up..."
    kill $APP_PID $DB_PID $SENTIMENT_PID $EMOTION_PID $PROPAGANDA_PID $SCRAPER_PID $FACTCHECK_PID 2>/dev/null
    unset DATABASE_URL
    unset SENTIMENT_URL
    unset EMOTION_URL
    unset PROPAGANDA_URL
    unset SCRAPER_URL
    unset FACTCHECK_URL
    exit 0
}

# Trap termination signals (e.g., SIGINT, SIGTERM) and call the cleanup function
trap cleanup SIGINT SIGTERM

# Start the main app
cd application
uvicorn app:app --reload --port 8010 &
APP_PID=$!

# Start database app
cd ../backend/database
uvicorn db_app:app --reload --port 8011 &
DB_PID=$!

# Start sentiment app
cd ../sentiment
uvicorn app:app --reload --port 8012 &
SENTIMENT_PID=$!

# Start emotion app
cd ../emotion
uvicorn app:app --reload --port 8013 &
EMOTION_PID=$!

# Start propaganda app
cd ../propaganda
uvicorn app:app --reload --port 8014 &
PROPAGANDA_PID=$!

# Start scraper app
cd ../scraper
gunicorn -w 4 -b 0.0.0.0:8015 app:app &
SCRAPER_PID=$!

# Start factcheck app
cd ../fact-check
uvicorn app.main:app --reload --port 8016 &
FACTCHECK_PID=$!

# Wait for all background processes to finish
wait $APP_PID $DB_PID $SENTIMENT_PID $EMOTION_PID $PROPAGANDA_PID $SCRAPER_PID $FACTCHECK_PID