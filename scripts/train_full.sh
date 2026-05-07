#!/usr/bin/env bash
LOGDIR=logs
mkdir -p $LOGDIR
TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
nohup python train_model.py > ${LOGDIR}/train_${TIMESTAMP}.out 2>&1 &
echo "Training started, logs at ${LOGDIR}/train_${TIMESTAMP}.out"
