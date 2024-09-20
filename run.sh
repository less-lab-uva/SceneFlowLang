#!/bin/bash

conda activate scene_flow

### Pull the data
source unpack_data.sh

python3 check_symbolic_properties.py -f ./study_data/scenarios/ -s ./results/
python3 check_symbolic_properties.py -f ./study_data/tcp/run1/ -s ./results/
python3 check_symbolic_properties.py -f ./study_data/lav/run1/ -s ./results/
python3 check_symbolic_properties.py -f ./study_data/interfuser/run1/ -s ./results/
