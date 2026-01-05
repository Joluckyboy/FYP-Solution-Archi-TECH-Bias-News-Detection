#!/bin/bash

# Function to kill process using a specific port
kill_port() {
    PORT=$1
    PID=$(lsof -t -i:$PORT)
    if [ -n "$PID" ]; then
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

# Start database app
cd database
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
wait $DB_PID $SENTIMENT_PID $EMOTION_PID $PROPAGANDA_PID $SCRAPER_PID 
# wait $DB_PID $SENTIMENT_PID $EMOTION_PID $PROPAGANDA_PID $SCRAPER_PID $FACTCHECK_PID