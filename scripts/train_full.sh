#!/bin/bash
# CTI-NLP - Full Training Script with Background Execution and Log Rotation
# Usage: ./scripts/train_full.sh [dataset_path] [sample_size]

set -e  # Exit on any error

# Default values
DATASET_PATH="${1:-data/datasets/url_dataset.csv}"
SAMPLE_SIZE="${2:-60000}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_DIR="logs"
BACKUP_DIR="backups"
PID_FILE="logs/training.pid"

# Create directories
mkdir -p "$LOG_DIR" "$BACKUP_DIR"

# Log file with timestamp
LOG_FILE="$LOG_DIR/training_$TIMESTAMP.log"

# Function to rotate old logs
rotate_logs() {
    echo "Rotating old logs..."
    # Keep last 10 log files
    ls -t "$LOG_DIR"/training_*.log | tail -n +11 | xargs -r rm
    
    # Archive logs older than 7 days
    find "$LOG_DIR" -name "training_*.log" -mtime +7 -exec gzip {} \;
}

# Function to backup current model
backup_model() {
    if [ -f "ml/saved_models/threat_pipeline.joblib" ]; then
        echo "Backing up current model..."
        cp ml/saved_models/threat_pipeline.joblib "$BACKUP_DIR/threat_pipeline_backup_$(date +%Y%m%d_%H%M%S).joblib"
    fi
}

# Function to handle cleanup on exit
cleanup() {
    echo "Cleaning up..."
    rm -f "$PID_FILE"
    if [ $? -eq 0 ]; then
        echo "Training completed successfully!"
    else
        echo "Training failed with exit code $?"
    fi
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Check if training is already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "Training is already running (PID: $PID)"
        echo "Check logs: $LOG_DIR/training_$(ls -t "$LOG_DIR"/training_*.log | head -1 | xargs basename -s .log).log"
        exit 1
    else
        echo "Stale PID file found, removing..."
        rm -f "$PID_FILE"
    fi
fi

# Start training
echo "Starting full dataset training..."
echo "Dataset: $DATASET_PATH"
echo "Sample size: $SAMPLE_SIZE"
echo "Log file: $LOG_FILE"
echo "PID file: $PID_FILE"

# Rotate logs and backup model
rotate_logs
backup_model

# Write PID file
echo $$ > "$PID_FILE"

# Create training command
TRAIN_CMD="cd backend && python train_model.py"

# Add custom dataset path if provided
if [ "$DATASET_PATH" != "data/datasets/url_dataset.csv" ]; then
    TRAIN_CMD="$TRAIN_CMD --input $DATASET_PATH"
fi

# Add custom sample size if provided
if [ "$SAMPLE_SIZE" != "60000" ]; then
    TRAIN_CMD="$TRAIN_CMD --sample-size $SAMPLE_SIZE"
fi

# Run training in background with nohup
echo "Executing: $TRAIN_CMD"
nohup bash -c "$TRAIN_CMD" > "$LOG_FILE" 2>&1 &

TRAIN_PID=$!
echo "Training started with PID: $TRAIN_PID"
echo "Monitor progress: tail -f $LOG_FILE"
echo "Stop training: kill $TRAIN_PID"
echo "Check status: ps -p $TRAIN_PID"

# Optional: Monitor for completion
if command -v notify-send >/dev/null 2>&1; then
    # Wait for training to complete and send notification
    (
        while ps -p $TRAIN_PID > /dev/null 2>&1; do
            sleep 30
        done
        notify-send "CTI-NLP Training" "Training completed! Check $LOG_FILE"
    ) &
fi

echo "Training script launched in background."
echo "Use 'tail -f $LOG_FILE' to monitor progress."
