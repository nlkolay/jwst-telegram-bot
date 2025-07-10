#!/bin/bash

LOG_FILE="bot_debug.log"
TIMEOUT_SECONDS=30

while true;
do
    # Ensure no other bot instances are running
    pkill -f "/home/niko/projects/jwst-telegram-bot/venv/bin/python bot.py" &>/dev/null
    sleep 1 # Give it a moment to terminate

    echo "$(date): Starting bot for $TIMEOUT_SECONDS seconds..." | tee -a "$LOG_FILE"
    timeout $TIMEOUT_SECONDS /home/niko/projects/jwst-telegram-bot/venv/bin/python bot.py &>> "$LOG_FILE"
    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 124 ]; then
        echo "$(date): Bot timed out after $TIMEOUT_SECONDS seconds." | tee -a "$LOG_FILE"
    elif [ $EXIT_CODE -ne 0 ]; then
        echo "$(date): Bot exited with error code $EXIT_CODE." | tee -a "$LOG_FILE"
    else
        echo "$(date): Bot exited gracefully." | tee -a "$LOG_FILE"
    fi

    echo "$(date): Waiting 30 seconds before next run..." | tee -a "$LOG_FILE"
    sleep 30
    echo "--------------------------------------------------" | tee -a "$LOG_FILE"
done