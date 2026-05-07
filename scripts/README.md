# CTI-NLP Training Scripts

This directory contains helper scripts for the ML training pipeline.

## Scripts Overview

### 1. chunked_feature_extraction.py
Precompute URL features in chunks with checkpoint support for large datasets.

**Usage:**
```bash
# Fresh extraction
python scripts/chunked_feature_extraction.py --input data/datasets/url_dataset.csv --output data/features/features.pkl

# Resume from checkpoint
python scripts/chunked_feature_extraction.py --resume data/features/checkpoint_000000.pkl

# Custom chunk size
python scripts/chunked_feature_extraction.py --input data/datasets/url_dataset.csv --output data/features/features.pkl --chunk-size 5000
```

**Features:**
- Chunked processing for memory efficiency
- Automatic checkpoint saving every N chunks
- Resume from latest checkpoint
- Progress tracking with tqdm
- Failed URL handling

### 2. train_full.sh
Shell script for background training with log rotation and model backups.

**Usage:**
```bash
# Default training
./scripts/train_full.sh

# Custom dataset and sample size
./scripts/train_full.sh data/datasets/custom_dataset.csv 100000

# Monitor progress
tail -f logs/training_YYYYMMDD_HHMMSS.log

# Stop training
kill $(cat logs/training.pid)
```

**Features:**
- Background execution with nohup
- Automatic log rotation (keeps 10 recent logs)
- Model backup before training
- PID file management
- Completion notifications (if notify-send available)

## Directory Structure

```
d:\NEW\
├── scripts/
│   ├── chunked_feature_extraction.py
│   ├── train_full.sh
│   └── README.md
├── backups/           # Manual model and dataset backups
├── logs/              # Training logs (auto-created)
└── data/
    ├── datasets/      # URL datasets
    └── features/      # Precomputed features (auto-created)
```

## Workflow Examples

### Large Dataset Training
```bash
# 1. Precompute features (optional but recommended for large datasets)
python scripts/chunked_feature_extraction.py --input data/datasets/large_dataset.csv --output data/features/large_features.pkl

# 2. Start background training
./scripts/train_full.sh data/datasets/large_dataset.csv 200000

# 3. Monitor progress
tail -f logs/training_$(ls -t logs/training_*.log | head -1 | xargs basename -s .log).log
```

### Resume Failed Training
```bash
# Check if training is still running
ps -p $(cat logs/training.pid) 2>/dev/null || echo "Training not running"

# Resume feature extraction from checkpoint
python scripts/chunked_feature_extraction.py --resume data/features/checkpoint_latest.pkl
```

## Backup Strategy

The `backups/` directory is used for:
- Manual model backups before retraining
- Dataset versioning
- Feature file snapshots

**Manual backup commands:**
```bash
# Backup current model
cp ml/saved_models/threat_pipeline.joblib backups/threat_pipeline_backup_$(date +%Y%m%d_%H%M%S).joblib

# Backup dataset
cp data/datasets/url_dataset.csv backups/url_dataset_backup_$(date +%Y%m%d_%H%M%S).csv
```

## Troubleshooting

### Common Issues

1. **Memory errors with large datasets**
   - Use chunked feature extraction with smaller chunk size
   - Reduce sample size in training script

2. **Training interruption**
   - Check logs in `logs/` directory
   - Resume from checkpoint if using chunked extraction
   - Verify PID file doesn't contain stale process

3. **Permission issues**
   - Make train_full.sh executable: `chmod +x scripts/train_full.sh`
   - Ensure write permissions to logs/ and backups/ directories

### Log Analysis
```bash
# View latest training log
tail -n 50 logs/training_$(ls -t logs/training_*.log | head -1 | xargs basename -s .log).log

# Search for errors in logs
grep -i error logs/training_*.log

# Monitor real-time progress
tail -f logs/training_*.log
```
