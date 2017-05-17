#!/bin/bash
# preprocessing wrapper script
# clears existing JSON files and checks if directories exist

mkdir -p ../data/images/themis_windowed

echo 'removing existing JSON files in data/jsons'
rm ../data/jsons/test_boxes.json
rm ../data/jsons/train_boxes.json
rm ../data/jsons/val_boxes.json

echo 'running generate_cratersets.py with default config file'
python generate_cratersets.py cfg/truth.cfg